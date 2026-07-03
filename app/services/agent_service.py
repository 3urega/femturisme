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

from .llm_service import build_provider, LLMResponse, ToolCall
from .tools       import ALL_TOOLS, execute_tool

# In-memory conversation store: session_id → list[dict]
# Replace with DB-backed storage for multi-server / persistence.
_history: dict[str, list[dict]] = {}

SYSTEM_PROMPT = """Ets un assistent turístic amable i expert de femturisme.cat, el portal de turisme de Catalunya i Andorra.
Ajudes els visitants a descobrir experiències, allotjaments, events, rutes i tot el que es pot fer arreu de Catalunya i Andorra.
Tens accés a eines per cercar informació actualitzada sobre destins, activitats i serveis turístics.
Respon sempre en l'idioma de l'usuari (català, castellà o anglès).
Quan presentis resultats, utilitza un format llegible amb els detalls més rellevants."""


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

        llm = build_provider(self.provider, current_app.config)

        for iteration in range(self.max_iterations):
            try:
                response: LLMResponse = llm.chat(
                    messages=self._with_system(history),
                    tools=ALL_TOOLS,
                )
            except Exception as exc:
                yield {'type': 'error', 'message': str(exc)}
                return

            if response.has_tool_calls:
                # ── Tool use turn ──────────────────────────────────────
                tool_results_content = []

                for tc in response.tool_calls:
                    yield {
                        'type':  'tool_call',
                        'tool':  tc.name,
                        'input': tc.input,
                    }

                    raw_result = execute_tool(tc.name, tc.input)

                    yield {
                        'type':   'tool_result',
                        'tool':   tc.name,
                        'result': json.loads(raw_result),
                    }

                    tool_results_content.append({
                        'type':        'tool_result',
                        'tool_use_id': tc.id,
                        'content':     raw_result,
                    })

                # Append assistant tool-use turn
                history.append({
                    'role':    'assistant',
                    'content': [
                        {'type': 'tool_use', 'id': tc.id, 'name': tc.name, 'input': tc.input}
                        for tc in response.tool_calls
                    ],
                })
                # Append tool results as user turn
                history.append({'role': 'user', 'content': tool_results_content})

            else:
                # ── Final answer ───────────────────────────────────────
                full_text = response.text

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

    def _with_system(self, history: list[dict]) -> list[dict]:
        return [{'role': 'system', 'content': SYSTEM_PROMPT}] + history


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
