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
from .llm_service import build_provider, LLMResponse, ToolCall
from .period_hints import (
    apply_event_period_hints,
    build_forced_search_events_input,
    infer_event_period,
    is_agenda_search_query,
)
from .language_guard import polish_reply_for_user
from .request_context import turn_user_message
from .tools       import ALL_TOOLS, execute_tool

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

    def run(self, user_message: str, session_id: str) -> Generator[dict, None, None]:
        """Generator that yields SSE-ready event dicts."""
        history = _get_history(session_id)

        # Add user turn
        history.append({'role': 'user', 'content': user_message})
        turn_user_message.set(user_message)
        current_user_message = user_message

        llm = build_provider(self.provider, current_app.config)

        for iteration in range(self.max_iterations):
            try:
                response: LLMResponse = llm.chat(
                    messages=self._with_system(history, current_user_message),
                    tools=ALL_TOOLS,
                )
            except Exception as exc:
                yield {'type': 'error', 'message': str(exc)}
                return

            if response.has_tool_calls:
                yield from self._handle_tool_calls(
                    response=response,
                    history=history,
                    current_user_message=current_user_message,
                )

            elif (
                iteration == 0
                and (forced_input := build_forced_search_events_input(current_user_message))
            ):
                yield from self._handle_forced_tool_call(
                    tool_name='search_events',
                    tool_input=forced_input,
                    history=history,
                    current_user_message=current_user_message,
                )

            else:
                # ── Final answer ───────────────────────────────────────
                full_text = polish_reply_for_user(current_user_message, response.text)

                # Simulate token streaming (replace with real streaming in phase 1)
                yield from _stream_text(full_text)

                history.append({'role': 'assistant', 'content': full_text})
                _save_history(session_id, history)

                yield {'type': 'done', 'full_text': full_text}
                return

        # Safety: max iterations reached
        msg = "He superat el màxim d'iteracions. Si us plau, reformula la pregunta."
        yield from _stream_text(msg)
        yield {'type': 'done', 'full_text': msg}

    @staticmethod
    def clear_history(session_id: str) -> None:
        _history.pop(session_id, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _with_system(
        self,
        history: list[dict],
        user_message: str | None = None,
    ) -> list[dict]:
        system = build_system_prompt()
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
            (tc, apply_event_period_hints(tc.name, tc.input, current_user_message))
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

    def _handle_forced_tool_call(
        self,
        *,
        tool_name: str,
        tool_input: dict,
        history: list[dict],
        current_user_message: str,
    ) -> Generator[dict, None, None]:
        tool_id = f'forced_{uuid.uuid4().hex[:12]}'
        resolved_input = apply_event_period_hints(
            tool_name,
            tool_input,
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

        history.append({
            'role':    'assistant',
            'content': [{
                'type':  'tool_use',
                'id':    tool_id,
                'name':  tool_name,
                'input': resolved_input,
            }],
        })
        history.append({
            'role': 'user',
            'content': [{
                'type':        'tool_result',
                'tool_use_id': tool_id,
                'content':     raw_result,
            }],
        })


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
