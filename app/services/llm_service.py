"""
Provider-agnostic LLM service.

Internal history format is Anthropic's (tool_use / tool_result blocks).
Each provider converts to its own wire format inside chat().

Supported providers: dummy | anthropic | openai | gemini
Default models:
  anthropic → claude-haiku-4-5-20251001
  openai    → gpt-4o-mini
  gemini    → gemini-2.0-flash
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Shared data structures
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    id:    str
    name:  str
    input: dict


@dataclass
class LLMResponse:
    stop_reason: str          # 'end_turn' | 'tool_use'
    text:        str = ''
    tool_calls:  list[ToolCall] = field(default_factory=list)

    @property
    def has_tool_calls(self):
        return self.stop_reason == 'tool_use' and bool(self.tool_calls)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class BaseLLMProvider:
    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Dummy provider
# ---------------------------------------------------------------------------

_TOOL_KEYWORDS: dict[str, list[str]] = {
    'search_destinations': [
        'on anar', 'destinació', 'destinacion', 'destination', 'poble', 'pobles',
        'municipi', 'municipio', 'comarca', 'lloc', 'llocs', 'visitar', 'besalú',
        'besalu', 'girona', 'empordà', 'emporda',
    ],
    'search_establishments': [
        'hotel', 'allotjament', 'alojamiento', 'accommodation', 'dormir', 'sleep',
        'hostal', 'hostel', 'casa rural', 'rural', 'camping', 'apartament',
        'restaurant', 'menjar', 'on menjar', 'on dormir', 'bar', 'cuina',
    ],
    'search_experiences': [
        'experiència', 'experiencias', 'experience', 'activitat', 'actividad',
        'activity', 'excursió', 'excursion', 'fer', 'hacer',
        'que fer', 'que hacer', 'turisme', 'turismo',
    ],
    'search_events': [
        'event', 'evento', 'festival', 'concert', 'fira', 'feria', 'fair',
        'agenda', 'calendari', 'calendar', 'festa', 'fiesta',
    ],
    'search_routes': [
        'ruta', 'rutes', 'route', 'routes', 'senderisme', 'hiking', 'trekking',
        'camí', 'camino', 'trail', 'bici', 'bicicleta', 'cycling',
    ],
}


class DummyProvider(BaseLLMProvider):
    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        if messages and isinstance(messages[-1].get('content'), list):
            if any(b.get('type') == 'tool_result' for b in messages[-1]['content']):
                return self._final(messages)

        user_text = self._last_user_text(messages)
        for tool_name, kws in _TOOL_KEYWORDS.items():
            if any(k in user_text.lower() for k in kws):
                return LLMResponse(
                    stop_reason='tool_use',
                    tool_calls=[ToolCall(id=str(uuid.uuid4()), name=tool_name,
                                         input={'destination': 'Catalunya'})],
                )
        return LLMResponse(stop_reason='end_turn',
                           text='Hola! Soc l\'assistent de femturisme.cat (mode dummy). '
                                'Pregunta\'m sobre rutes, events, allotjaments o experiències!')

    def _last_user_text(self, messages):
        for m in reversed(messages):
            if m['role'] == 'user':
                c = m['content']
                if isinstance(c, str):
                    return c
                if isinstance(c, list):
                    return ' '.join(b.get('text', '') for b in c if b.get('type') == 'text')
        return ''

    def _final(self, messages):
        for m in reversed(messages):
            if not isinstance(m.get('content'), list):
                continue
            for b in m['content']:
                if b.get('type') == 'tool_result':
                    try:
                        data = json.loads(b['content'])
                        items = data.get('results', [])
                        lines = ['Aquí tens el que he trobat:\n']
                        for it in items[:5]:
                            lines.append(f"**{it.get('title', it.get('name', '—'))}**")
                            if it.get('location'):
                                lines.append(f"  📍 {it['location']}")
                            if it.get('description'):
                                lines.append(f"  {it['description'][:120]}…")
                            lines.append('')
                        return LLMResponse(stop_reason='end_turn', text='\n'.join(lines))
                    except Exception:
                        pass
        return LLMResponse(stop_reason='end_turn', text='He trobat alguns resultats a femturisme.cat.')


# ---------------------------------------------------------------------------
# Anthropic  (claude-haiku-4-5-20251001 default — no thinking on Haiku)
# ---------------------------------------------------------------------------

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = model

    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        system   = None
        filtered = []
        for m in messages:
            if m['role'] == 'system':
                system = m['content']
            else:
                filtered.append(m)

        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=2048,
            messages=filtered,
            tools=tools,
        )
        if system:
            kwargs['system'] = system

        response = self.client.messages.create(**kwargs)

        if response.stop_reason == 'tool_use':
            calls = [
                ToolCall(id=b.id, name=b.name, input=b.input)
                for b in response.content
                if b.type == 'tool_use'
            ]
            return LLMResponse(stop_reason='tool_use', tool_calls=calls)

        text = next((b.text for b in response.content if b.type == 'text'), '')
        return LLMResponse(stop_reason='end_turn', text=text)


# ---------------------------------------------------------------------------
# OpenAI  (gpt-4o-mini default)
# History conversion: Anthropic tool_use/tool_result blocks → OpenAI format
# ---------------------------------------------------------------------------

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model  = model

    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        oai_messages = self._convert_messages(messages)
        oai_tools = [
            {'type': 'function', 'function': {
                'name':        t['name'],
                'description': t['description'],
                'parameters':  t['input_schema'],
            }}
            for t in tools
        ] or None

        response = self.client.chat.completions.create(
            model=self.model,
            messages=oai_messages,
            tools=oai_tools,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments),
                )
                for tc in msg.tool_calls
            ]
            return LLMResponse(stop_reason='tool_use', tool_calls=calls)

        return LLMResponse(stop_reason='end_turn', text=msg.content or '')

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        """Anthropic-format history → OpenAI wire format."""
        out = []
        for m in messages:
            role    = m['role']
            content = m['content']

            if role == 'system':
                out.append({'role': 'system', 'content': content})

            elif role == 'user':
                if isinstance(content, str):
                    out.append({'role': 'user', 'content': content})
                else:
                    tool_results = [b for b in content if b.get('type') == 'tool_result']
                    if tool_results:
                        # One OpenAI 'tool' message per result
                        for tr in tool_results:
                            out.append({
                                'role':         'tool',
                                'tool_call_id': tr['tool_use_id'],
                                'content':      tr['content'],
                            })
                    else:
                        text = ' '.join(b.get('text', '') for b in content
                                        if b.get('type') == 'text')
                        out.append({'role': 'user', 'content': text})

            elif role == 'assistant':
                if isinstance(content, str):
                    out.append({'role': 'assistant', 'content': content})
                else:
                    tool_uses = [b for b in content if b.get('type') == 'tool_use']
                    if tool_uses:
                        out.append({
                            'role':       'assistant',
                            'content':    None,
                            'tool_calls': [
                                {
                                    'id':   b['id'],
                                    'type': 'function',
                                    'function': {
                                        'name':      b['name'],
                                        'arguments': json.dumps(b['input']),
                                    },
                                }
                                for b in tool_uses
                            ],
                        })
                    else:
                        text = ' '.join(b.get('text', '') for b in content
                                        if b.get('type') == 'text')
                        out.append({'role': 'assistant', 'content': text})
        return out


# ---------------------------------------------------------------------------
# Gemini  (gemini-3.1-flash-lite default)
#
# Thought-signature fix: thinking-enabled Gemini models attach a thought_signature
# to FunctionCall parts. Rebuilding those protos from Anthropic-format history
# loses the signature and causes a 400 error.
#
# Solution: keep the chat object alive within one agent run() so tool results
# are sent via the live chat (signatures stay in its internal state).
# For cross-turn history (previous run()s), tool_use+tool_result pairs are
# dropped and only text messages are passed — they can't be safely recreated.
# ---------------------------------------------------------------------------

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai      = genai
        self.model_name = model
        self._chat      = None   # kept alive within one AgentService.run() call

    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        last = messages[-1] if messages else {}
        is_tool_result = (
            self._chat is not None
            and isinstance(last.get('content'), list)
            and any(b.get('type') == 'tool_result' for b in last['content'])
        )

        if is_tool_result:
            # Continue the live chat — thought_signatures are preserved in its state
            return self._send_tool_results(messages)

        # Fresh start: build a new chat from safe history (text turns only)
        fn_decls = [self._fn_decl(t) for t in tools]
        model = self.genai.GenerativeModel(
            self.model_name,
            tools=[self.genai.protos.Tool(function_declarations=fn_decls)],
        )
        safe_history, last_text = self._safe_history(messages)
        self._chat = model.start_chat(history=safe_history)
        resp = self._chat.send_message(last_text)
        return self._parse(resp)

    def _send_tool_results(self, messages: list[dict]) -> LLMResponse:
        """Feed FunctionResponse parts into the live chat (no history rebuild)."""
        # Resolve tool_use_id → name from the preceding assistant turn
        name_by_id: dict[str, str] = {}
        for m in reversed(messages[:-1]):
            if m['role'] == 'assistant' and isinstance(m.get('content'), list):
                for b in m['content']:
                    if b.get('type') == 'tool_use':
                        name_by_id[b['id']] = b['name']
                break

        parts = []
        for b in messages[-1]['content']:
            if b.get('type') != 'tool_result':
                continue
            name = name_by_id.get(b['tool_use_id'], 'tool')
            try:
                data = json.loads(b['content'])
            except Exception:
                data = {'output': b['content']}
            parts.append(self.genai.protos.Part(
                function_response=self.genai.protos.FunctionResponse(
                    name=name, response=data,
                )
            ))

        resp = self._chat.send_message(parts)
        return self._parse(resp)

    def _safe_history(self, messages: list[dict]):
        """
        Convert Anthropic history → Gemini format for start_chat().
        Tool use + tool result pairs are skipped (can't recreate thought_signatures).
        Only plain text turns (user queries + assistant final answers) are kept.
        """
        result = []
        system_text = None
        msgs = messages[:-1]   # last message is sent via send_message
        i = 0

        while i < len(msgs):
            m = msgs[i]
            role, content = m['role'], m['content']

            if role == 'system':
                system_text = content
                i += 1

            elif role == 'user' and isinstance(content, str):
                text = f"{system_text}\n\n{content}" if system_text else content
                system_text = None
                result.append({'role': 'user', 'parts': [text]})
                i += 1

            elif role == 'assistant' and isinstance(content, str):
                result.append({'role': 'model', 'parts': [content]})
                i += 1

            elif role == 'assistant' and isinstance(content, list):
                # Tool use turn — skip it AND the following tool_result user turn
                i += 1
                if (i < len(msgs)
                        and msgs[i]['role'] == 'user'
                        and isinstance(msgs[i].get('content'), list)
                        and any(b.get('type') == 'tool_result'
                                for b in msgs[i]['content'])):
                    i += 1

            else:
                i += 1

        # Prepare the last (new) user message
        last = messages[-1]
        last_content = last.get('content', '')
        last_text = last_content if isinstance(last_content, str) else ''
        if system_text and last_text:
            last_text = f"{system_text}\n\n{last_text}"

        return result, last_text

    def _parse(self, resp) -> LLMResponse:
        try:
            part = resp.candidates[0].content.parts[0]
        except (IndexError, AttributeError):
            return LLMResponse(stop_reason='end_turn', text='')

        if hasattr(part, 'function_call') and part.function_call.name:
            fc = part.function_call
            return LLMResponse(
                stop_reason='tool_use',
                tool_calls=[ToolCall(id=str(uuid.uuid4()),
                                     name=fc.name,
                                     input=dict(fc.args))],
            )
        return LLMResponse(stop_reason='end_turn', text=getattr(part, 'text', '') or '')

    def _fn_decl(self, t: dict):
        return self.genai.protos.FunctionDeclaration(
            name=t['name'],
            description=t['description'],
            parameters=self._to_schema(t['input_schema']),
        )

    def _to_schema(self, schema: dict):
        props = {}
        for k, v in schema.get('properties', {}).items():
            t = v.get('type', 'string').upper()
            props[k] = self.genai.protos.Schema(
                type=getattr(self.genai.protos.Type, t, self.genai.protos.Type.STRING),
                description=v.get('description', ''),
            )
        return self.genai.protos.Schema(
            type=self.genai.protos.Type.OBJECT,
            properties=props,
            required=schema.get('required', []),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_provider(provider: str, config: dict) -> BaseLLMProvider:
    if provider == 'anthropic':
        return AnthropicProvider(
            api_key=config['ANTHROPIC_API_KEY'],
            model=config['ANTHROPIC_MODEL'],
        )
    if provider == 'openai':
        return OpenAIProvider(
            api_key=config['OPENAI_API_KEY'],
            model=config['OPENAI_MODEL'],
        )
    if provider == 'gemini':
        return GeminiProvider(
            api_key=config['GEMINI_API_KEY'],
            model=config['GEMINI_MODEL'],
        )
    return DummyProvider()
