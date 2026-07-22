"""Run 10 CA-mapped demo questions against /api/chat and print evidence."""
from __future__ import annotations

import json
import re
import sys
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5010'
OUT = Path(__file__).resolve().parent / 'demo_ca_battery_results.txt'

CASES = [
    {
        'id': 'D01',
        'ca': 'CA-01',
        'rf': 'RF-01',
        'label': 'Llenguatge natural',
        'messages': ['Hola, em pots ajudar a planificar un cap de setmana al Berguedà?'],
    },
    {
        'id': 'D02',
        'ca': 'CA-02',
        'rf': 'RF-02',
        'label': 'Intenció — rutes',
        'messages': ['Quines rutes de senderisme hi ha al Berguedà?'],
        'expect_tools': ['search_routes'],
    },
    {
        'id': 'D03',
        'ca': 'CA-02',
        'rf': 'RF-02',
        'label': 'Intenció — agenda (no experiències)',
        'messages': ['Què fer aquest cap de setmana a Girona?'],
        'expect_tools': ['search_events'],
    },
    {
        'id': 'D04',
        'ca': 'CA-04',
        'rf': 'RF-04',
        'label': 'Combinació fonts — dormir + fer',
        'messages': ['On puc dormir i què fer aquest cap de setmana a Girona?'],
        'expect_tools_any': [['search_establishments', 'search_events']],
    },
    {
        'id': 'D05',
        'ca': 'CA-05',
        'rf': 'RF-11',
        'label': 'Enllaços femturisme.cat',
        'messages': ['Recomana’m hotels a Barcelona'],
        'expect_links': True,
    },
    {
        'id': 'D06',
        'ca': 'CA-06',
        'rf': 'RF-08',
        'label': 'Sense coincidències — plat específic',
        'messages': ['On menjar uns bons macarrons a Besalú?'],
    },
    {
        'id': 'D07',
        'ca': 'CA-07',
        'rf': 'RF-06',
        'label': 'Context conversacional Patum → Berga',
        'session': True,
        'messages': [
            'Què en saps de la Patum?',
            'buscam allotjament a prop de Berga',
            'si, 30 km',
        ],
        'expect_last_tools': ['search_establishments'],
    },
    {
        'id': 'D08',
        'ca': 'CA-08',
        'rf': 'RF-08',
        'label': 'No inventar — tema sense catàleg',
        'messages': ['Quin és el millor restaurant de la galàxia a Catalunya?'],
    },
    {
        'id': 'D09',
        'ca': 'CA-02',
        'rf': 'RF-02',
        'label': 'Articles temàtics (recall Patum)',
        'messages': ['Què és la Patum?'],
        'expect_tools_any': [['search_articles', 'search_events']],
    },
    {
        'id': 'D10',
        'ca': 'CA-02',
        'rf': 'RF-10',
        'label': 'Idioma castellà',
        'messages': ['¿Qué rutas hay en la Costa Brava?'],
        'expect_tools': ['search_routes'],
    },
]


@dataclass
class TurnOut:
    message: str
    tools: list[str] = field(default_factory=list)
    text: str = ''
    error: str | None = None


@dataclass
class CaseOut:
    case_id: str
    ca: str
    rf: str
    label: str
    turns: list[TurnOut] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / '.env')


def _post_chat(message: str, session_id: str) -> TurnOut:
    turn = TurnOut(message=message)
    url = f"{BASE.rstrip('/')}/api/chat"
    body = json.dumps({'message': message, 'session_id': session_id}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        turn.error = f'HTTP {exc.code}'
        return turn
    except Exception as exc:  # noqa: BLE001
        turn.error = str(exc)
        return turn

    buffer = raw
    while '\n\n' in buffer:
        block, buffer = buffer.split('\n\n', 1)
        for line in block.split('\n'):
            if not line.startswith('data: '):
                continue
            payload = line[6:].strip()
            if not payload or payload == '[DONE]':
                continue
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if ev.get('type') == 'tool_call':
                tool = ev.get('tool')
                if tool:
                    turn.tools.append(tool)
            elif ev.get('type') == 'text_chunk':
                turn.text += ev.get('content', ev.get('text', ''))
            elif ev.get('type') == 'done':
                turn.text = turn.text or ev.get('full_text', '')
            elif ev.get('type') == 'error':
                turn.error = ev.get('message')
    turn.text = turn.text.strip()
    return turn


def _has_femturisme_links(text: str) -> bool:
    return bool(re.search(r'https?://(?:www\.)?femturisme\.cat/', text, re.I))


def _evaluate(case: dict, case_out: CaseOut) -> None:
    if case_out.turns and case_out.turns[-1].error:
        case_out.notes.append(f"ERROR: {case_out.turns[-1].error}")
        return

    if expect := case.get('expect_tools'):
        last_tools = case_out.turns[-1].tools
        if not any(t in last_tools for t in expect):
            case_out.notes.append(f"Tools esperades {expect}, obtingut {last_tools}")

    if groups := case.get('expect_tools_any'):
        last_tools = set(case_out.turns[-1].tools)
        if not any(set(g).issubset(last_tools) for g in groups):
            case_out.notes.append(f"Tools insuficients: {case_out.turns[-1].tools}")

    if case.get('expect_last_tools'):
        last_tools = case_out.turns[-1].tools
        for tool in case['expect_last_tools']:
            if tool not in last_tools:
                case_out.notes.append(f"Últim torn sense {tool}: {last_tools}")

    if case.get('expect_links'):
        full_text = '\n'.join(t.text for t in case_out.turns)
        if not _has_femturisme_links(full_text):
            case_out.notes.append('Cap enllaç femturisme.cat a la resposta')

    if not case_out.notes:
        case_out.notes.append('OK — evidència alineada amb el criteri')


def run_case(case: dict) -> CaseOut:
    session_id = str(uuid.uuid4())
    out = CaseOut(
        case_id=case['id'],
        ca=case['ca'],
        rf=case['rf'],
        label=case['label'],
    )
    for message in case['messages']:
        sid = session_id if case.get('session') else str(uuid.uuid4())
        turn = _post_chat(message, sid)
        out.turns.append(turn)
        if turn.error:
            break
    _evaluate(case, out)
    return out


def _truncate(text: str, limit: int = 600) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + '...'


def main() -> int:
    _load_env()
    lines: list[str] = [f'Demo CA battery — base={BASE}', '=' * 72, '']
    results: list[CaseOut] = []

    for case in CASES:
        print(f"Running {case['id']} ({case['ca']})...")
        result = run_case(case)
        results.append(result)
        lines.append(f"## {result.case_id} — {result.ca} / {result.rf} — {result.label}")
        for index, turn in enumerate(result.turns, 1):
            lines.append(f"Pregunta {index}: {turn.message}")
            lines.append(f"  Eines: {', '.join(turn.tools) or '(cap)'}")
            if turn.error:
                lines.append(f"  Error: {turn.error}")
            else:
                lines.append(f"  Resposta: {_truncate(turn.text)}")
        lines.append(f"  Verificació: {result.notes[0] if result.notes else '—'}")
        lines.append('')

    ok = sum(1 for r in results if r.notes and r.notes[0].startswith('OK'))
    lines.append('=' * 72)
    lines.append(f'Resum: {ok}/{len(results)} casos amb evidència OK')
    text = '\n'.join(lines) + '\n'
    OUT.write_text(text, encoding='utf-8')
    print(text)
    print(f'Guardat a {OUT}')
    return 0 if ok == len(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
