"""
AgentService — orchestrates the tool-use loop and conversation history.

Flow per turn:
  1. Append user message to history
  2. Call LLM with full history + tool schemas
  3. If stop_reason == 'tool_use':
       a. Yield tool_call event (UI shows "searching…")
       b. Execute tool, yield tool_result event
       c. Append both assistant turn and tool result to history
       d. Loop back to step 2
  4. When stop_reason == 'end_turn':
       a. Yield text_chunk events (simulated streaming)
       b. Append assistant answer to history
       c. Yield done event
"""
from __future__ import annotations
import json
import time
import uuid
from typing import Generator

from flask import current_app

from app.prompts.femturisme import build_system_prompt
from app.services.chat_context import AgentContext, PageContext
from .llm_service import build_provider, LLMResponse, ToolCall
from .period_hints import (
    apply_event_period_hints,
    build_forced_search_events_input,
    infer_event_period,
    is_agenda_search_query,
)
from .query_keywords import (
    build_forced_keyword_tool_calls,
    primary_search_keyword,
)
from .language_guard import polish_reply_for_user
from .request_context import turn_user_language, turn_user_message
from .request_logging import log_chat_turn, log_error
from .user_language import detect_user_language
from .tools       import CATALOG_TOOLS, execute_tool, _inject_catalog_lang

# In-memory conversation store: session_id → list[dict]
# Replace with DB-backed storage for multi-server / persistence.
_history: dict[str, list[dict]] = {}


class AgentService:

    def __init__(self, provider: str = 'dummy', max_iterations: int = 5):
        self.provider       = provider
        self.max_iterations = max_iterations

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        user_message: str,
        session_id: str,
        *,
        page_context: PageContext | None = None,
        agent_context: AgentContext | None = None,
    ) -> Generator[dict, None, None]:
        """Generator that yields SSE-ready event dicts."""
        if agent_context is None:
            agent_context = AgentContext()
        history = _get_history(session_id)

        # Add user turn
        history.append({'role': 'user', 'content': user_message})
        user_language = detect_user_language(user_message)
        turn_user_message.set(user_message)
        turn_user_language.set(user_language)
        current_user_message = user_message
        turn_started = time.perf_counter()

        llm = build_provider(self.provider, current_app.config)

        for iteration in range(self.max_iterations):
            try:
                response: LLMResponse = llm.chat(
                    messages=self._with_system(
                        history,
                        current_user_message,
                        page_context=page_context,
                        agent_context=agent_context,
                    ),
                    tools=CATALOG_TOOLS,
                )
            except Exception as exc:
                log_error(session_id=session_id, message=str(exc), exc=exc)
                self._log_turn_end(
                    session_id=session_id,
                    agent_context=agent_context,
                    user_language=user_language,
                    turn_started=turn_started,
                    status='error',
                )
                yield {'type': 'error', 'message': str(exc)}
                return

            if response.has_tool_calls:
                yield from self._handle_tool_calls(
                    response=response,
                    history=history,
                    current_user_message=current_user_message,
                )

            elif iteration == 0 and agent_context.mode == 'femturisme':
                if forced_events := build_forced_search_events_input(current_user_message):
                    if kw := primary_search_keyword(current_user_message):
                        forced_events['query'] = kw
                    yield from self._handle_forced_tool_calls(
                        calls=[('search_events', forced_events)],
                        history=history,
                        current_user_message=current_user_message,
                    )
                elif forced_keyword := build_forced_keyword_tool_calls(current_user_message):
                    yield from self._handle_forced_tool_calls(
                        calls=forced_keyword,
                        history=history,
                        current_user_message=current_user_message,
                    )
                else:
                    yield from self._emit_final_answer(
                        response=response,
                        history=history,
                        session_id=session_id,
                        agent_context=agent_context,
                        user_language=user_language,
                        turn_started=turn_started,
                        current_user_message=current_user_message,
                    )
                    return

            else:
                yield from self._emit_final_answer(
                    response=response,
                    history=history,
                    session_id=session_id,
                    agent_context=agent_context,
                    user_language=user_language,
                    turn_started=turn_started,
                    current_user_message=current_user_message,
                )
                return

        # Safety: max iterations reached
        msg = "He superat el màxim d'iteracions. Si us plau, reformula la pregunta."
        yield from _stream_text(msg)
        self._log_turn_end(
            session_id=session_id,
            agent_context=agent_context,
            user_language=user_language,
            turn_started=turn_started,
            status='max_iterations',
        )
        yield {'type': 'done', 'full_text': msg}

    @staticmethod
    def clear_history(session_id: str) -> None:
        _history.pop(session_id, None)

    @staticmethod
    def _log_turn_end(
        *,
        session_id: str,
        agent_context: AgentContext,
        user_language: str,
        turn_started: float,
        status: str,
    ) -> None:
        duration_ms = (time.perf_counter() - turn_started) * 1000
        log_chat_turn(
            session_id=session_id,
            duration_ms=duration_ms,
            language=user_language,
            operational_mode=agent_context.mode,
            entity_id=agent_context.entity_id,
            status=status,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _with_system(
        self,
        history: list[dict],
        user_message: str | None = None,
        *,
        page_context: PageContext | None = None,
        agent_context: AgentContext | None = None,
    ) -> list[dict]:
        if agent_context is None:
            agent_context = AgentContext()
        system = build_system_prompt(
            page_context=page_context,
            agent_context=agent_context,
            user_language=turn_user_language.get() or 'ca',
        )
        if user_message and is_agenda_search_query(user_message):
            period = infer_event_period(user_message)
            system += (
                "\n\n## Instrucció d'aquest torn\n"
                "L'usuari demana l'agenda del catàleg. **Has de cridar `search_events`** "
                "abans de respondre; no diguis que no hi ha esdeveniments sense consultar l'eina.\n"
            )
            if period is not None:
                system += (
                    f"- Període detectat: `date_from: {period[0]}`, `date_to: {period[1]}`\n"
                )
        return [{'role': 'system', 'content': system}] + history

    def _handle_tool_calls(
        self,
        *,
        response: LLMResponse,
        history: list[dict],
        current_user_message: str,
    ) -> Generator[dict, None, None]:
        tool_results_content = []

        resolved_calls = [
            (
                tc,
                apply_event_period_hints(
                    tc.name,
                    _inject_catalog_lang(tc.name, dict(tc.input or {})),
                    current_user_message,
                ),
            )
            for tc in response.tool_calls
        ]

        for tc, tool_input in resolved_calls:
            yield {
                'type':  'tool_call',
                'tool':  tc.name,
                'input': tool_input,
            }

            try:
                raw_result = execute_tool(
                    tc.name,
                    tool_input,
                    user_message=current_user_message,
                )
                parsed = json.loads(raw_result)
            except Exception as exc:
                parsed = {
                    'error': f"Error executant {tc.name}: {exc}",
                    'results': [],
                }
                raw_result = json.dumps(parsed, ensure_ascii=False)

            yield {
                'type':   'tool_result',
                'tool':   tc.name,
                'result': parsed,
            }

            tool_results_content.append({
                'type':        'tool_result',
                'tool_use_id': tc.id,
                'content':     raw_result,
            })

        history.append({
            'role':    'assistant',
            'content': [
                {'type': 'tool_use', 'id': tc.id, 'name': tc.name, 'input': tool_input}
                for tc, tool_input in resolved_calls
            ],
        })
        history.append({'role': 'user', 'content': tool_results_content})

    def _emit_final_answer(
        self,
        *,
        response: LLMResponse,
        history: list[dict],
        session_id: str,
        agent_context: AgentContext,
        user_language: str,
        turn_started: float,
        current_user_message: str,
    ) -> Generator[dict, None, None]:
        full_text = polish_reply_for_user(current_user_message, response.text)
        yield from _stream_text(full_text)
        history.append({'role': 'assistant', 'content': full_text})
        _save_history(session_id, history)
        self._log_turn_end(
            session_id=session_id,
            agent_context=agent_context,
            user_language=user_language,
            turn_started=turn_started,
            status='ok',
        )
        yield {'type': 'done', 'full_text': full_text}

    def _handle_forced_tool_calls(
        self,
        *,
        calls: list[tuple[str, dict]],
        history: list[dict],
        current_user_message: str,
    ) -> Generator[dict, None, None]:
        if not calls:
            return

        assistant_content = []
        tool_results_content = []

        for tool_name, tool_input in calls:
            tool_id = f'forced_{uuid.uuid4().hex[:12]}'
            resolved_input = apply_event_period_hints(
                tool_name,
                _inject_catalog_lang(tool_name, dict(tool_input or {})),
                current_user_message,
            )

            yield {
                'type':  'tool_call',
                'tool':  tool_name,
                'input': resolved_input,
            }

            try:
                raw_result = execute_tool(
                    tool_name,
                    resolved_input,
                    user_message=current_user_message,
                )
                parsed = json.loads(raw_result)
            except Exception as exc:
                parsed = {
                    'error': f"Error executant {tool_name}: {exc}",
                    'results': [],
                }
                raw_result = json.dumps(parsed, ensure_ascii=False)

            yield {
                'type':   'tool_result',
                'tool':   tool_name,
                'result': parsed,
            }

            assistant_content.append({
                'type':  'tool_use',
                'id':    tool_id,
                'name':  tool_name,
                'input': resolved_input,
            })
            tool_results_content.append({
                'type':        'tool_result',
                'tool_use_id': tool_id,
                'content':     raw_result,
            })

        history.append({'role': 'assistant', 'content': assistant_content})
        history.append({'role': 'user', 'content': tool_results_content})


# ---------------------------------------------------------------------------
# History helpers
# ---------------------------------------------------------------------------

def _get_history(session_id: str) -> list[dict]:
    if session_id not in _history:
        _history[session_id] = []
    return _history[session_id]


def _save_history(session_id: str, history: list[dict]) -> None:
    _history[session_id] = history


# ---------------------------------------------------------------------------
# Simulated text streaming
# ---------------------------------------------------------------------------

def _stream_text(text: str, chunk_size: int = 4) -> Generator[dict, None, None]:
    """Yields text in small chunks to simulate token streaming."""
    words = text.split(' ')
    buffer = []
    for word in words:
        buffer.append(word)
        if len(buffer) >= chunk_size:
            yield {'type': 'text_chunk', 'content': ' '.join(buffer) + ' '}
            buffer = []
            time.sleep(0.03)
    if buffer:
        yield {'type': 'text_chunk', 'content': ' '.join(buffer)}
