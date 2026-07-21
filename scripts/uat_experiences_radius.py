"""Issue #44 — UAT radi experiències: Calella + 50 km + visites guiades."""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = Path(__file__).resolve().parent / 'uat_experiences_radius_results.txt'
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5010'
EXPECTED_TOOL = 'search_experiences'
URL_PREFIX = 'https://www.femturisme.cat/ofertes/'

CASES: list[dict] = [
    {
        'id': 'UAT-EXP-R01',
        'description': 'km explícit al primer missatge (paritat portal)',
        'turns': [
            {'message': 'Visitas guiadas a 50 km de Calella'},
        ],
        'expect_distance_km': 50,
        'destination_needle': 'calella',
        'min_total': 1,
    },
    {
        'id': 'UAT-EXP-R02',
        'description': 'proximitat sense km -> dialog -> radi (#43)',
        'turns': [
            {
                'message': (
                    "M'agradaria fer visites guiades des de Calella "
                    'sense allunyar-me gaire'
                ),
                'expect_clarification': True,
            },
            {
                'message': '50 km',
                'expect_distance_km': 50,
                'destination_needle': 'calella',
                'min_total': 1,
            },
        ],
    },
]


@dataclass
class TurnResult:
    message: str
    tools_called: list[str] = field(default_factory=list)
    tool_inputs: dict[str, dict] = field(default_factory=dict)
    tool_totals: dict[str, int] = field(default_factory=dict)
    tool_results: dict[str, dict] = field(default_factory=dict)
    text: str = ''
    error: str | None = None


@dataclass
class CaseResult:
    case_id: str
    description: str
    turns: list[TurnResult] = field(default_factory=list)
    distance_km_seen: int | None = None
    first_url: str | None = None
    first_title: str | None = None
    meta_scope: str | None = None
    pass_: bool = False
    detail: str = ''


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / '.env')


def _env(name: str, *fallbacks: str) -> str:
    for key in (name, *fallbacks):
        value = os.environ.get(key, '').strip()
        if value:
            return value
    return ''


def mysql_available() -> bool:
    host = _env('AGENT_MYSQL_HOST', 'MYSQL_HOST')
    user = _env('AGENT_MYSQL_USER', 'MYSQL_USER')
    return bool(host and user)


def _normalize(text: str) -> str:
    lowered = (text or '').lower()
    decomposed = unicodedata.normalize('NFD', lowered)
    return ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn')


def _parse_total(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_distance_km(value: object) -> int | None:
    parsed = _parse_total(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


def _post_chat(message: str, session_id: str, base: str) -> tuple[int, str | None]:
    url = f"{base.rstrip('/')}/api/chat"
    body = json.dumps({'message': message, 'session_id': session_id}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode('utf-8', errors='replace')
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def run_turn(message: str, session_id: str, base: str) -> TurnResult:
    result = TurnResult(message=message)
    status, raw = _post_chat(message, session_id, base)
    if status != 200:
        result.error = f'HTTP {status}' if status else (raw or 'request failed')
        return result

    buffer = raw or ''
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
            event_type = ev.get('type')
            if event_type == 'tool_call':
                tool = ev.get('tool', '')
                if tool:
                    result.tools_called.append(tool)
                tool_input = ev.get('input')
                if isinstance(tool_input, dict):
                    result.tool_inputs[tool] = tool_input
            elif event_type == 'tool_result':
                tool = ev.get('tool', '')
                payload_result = ev.get('result', {})
                if isinstance(payload_result, dict):
                    total = _parse_total(payload_result.get('total'))
                    if total is not None:
                        result.tool_totals[tool] = total
                    result.tool_results[tool] = payload_result
            elif event_type == 'text_chunk':
                result.text += ev.get('content', ev.get('text', ''))
            elif event_type == 'done':
                result.text = result.text or ev.get('full_text', '')
            elif event_type == 'error':
                result.error = ev.get('message')

    result.text = result.text.strip()
    return result


def _destination_ok(tool_input: dict | None, needle: str) -> bool:
    if not tool_input or not needle:
        return True
    destination = _normalize(str(tool_input.get('destination', '')))
    return needle in destination


def _asks_for_km(text: str) -> bool:
    normalized = _normalize(text)
    patterns = (
        r'\bquants km\b',
        r'\bquants quilometres\b',
        r'\bquants quilometres\b',
        r'\bcuants km\b',
        r'\bcuantos km\b',
        r'\bhow many km\b',
        r'\bcombien de km\b',
        r'\bradi\b',
        r'\bdistancia\b',
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _turn1_clarification_ok(turn: TurnResult) -> bool:
    if turn.error:
        return False
    exp_input = turn.tool_inputs.get(EXPECTED_TOOL, {})
    distance = _parse_distance_km(exp_input.get('distance_km'))
    if EXPECTED_TOOL not in turn.tools_called:
        return _asks_for_km(turn.text)
    if distance is None:
        return _asks_for_km(turn.text) or True
    return False


def _evaluate_search_turn(
    turn: TurnResult,
    *,
    expect_distance_km: int | None,
    destination_needle: str,
    min_total: int,
) -> tuple[bool, str, int | None, str | None, str | None, str | None]:
    if turn.error:
        return False, f'error: {turn.error}', None, None, None, None

    if EXPECTED_TOOL not in turn.tools_called:
        tools = ', '.join(turn.tools_called) or '(cap)'
        return False, f'expected {EXPECTED_TOOL}, got {tools}', None, None, None, None

    tool_input = turn.tool_inputs.get(EXPECTED_TOOL, {})
    distance_km = _parse_distance_km(tool_input.get('distance_km'))
    if expect_distance_km is not None:
        if distance_km is None:
            return False, 'missing distance_km in tool input', distance_km, None, None, None
        if distance_km != expect_distance_km:
            return (
                False,
                f'distance_km={distance_km}, expected {expect_distance_km}',
                distance_km,
                None,
                None,
                None,
            )

    if not _destination_ok(tool_input, destination_needle):
        return (
            False,
            f"destination={tool_input.get('destination')!r} missing {destination_needle!r}",
            distance_km,
            None,
            None,
            None,
        )

    total = turn.tool_totals.get(EXPECTED_TOOL, 0)
    if total < min_total:
        return False, f'total={total} < min_total={min_total}', distance_km, None, None, None

    payload = turn.tool_results.get(EXPECTED_TOOL, {})
    meta = payload.get('meta') if isinstance(payload, dict) else None
    meta_scope = meta.get('scope') if isinstance(meta, dict) else None

    cards = payload.get('results') if isinstance(payload, dict) else None
    first_url = None
    first_title = None
    if isinstance(cards, list) and cards and isinstance(cards[0], dict):
        first_url = str(cards[0].get('url') or '') or None
        first_title = str(cards[0].get('title') or '') or None

    if not first_url or not first_url.startswith(URL_PREFIX):
        return (
            False,
            f'first url invalid: {first_url or "—"}',
            distance_km,
            first_url,
            first_title,
            meta_scope,
        )

    return True, 'ok', distance_km, first_url, first_title, meta_scope


def evaluate_case(case: dict, turns: list[TurnResult]) -> CaseResult:
    result = CaseResult(case_id=case['id'], description=case['description'], turns=turns)

    if case['id'] == 'UAT-EXP-R01':
        if not turns:
            result.detail = 'missing turn'
            return result
        ok, detail, distance_km, first_url, first_title, meta_scope = _evaluate_search_turn(
            turns[0],
            expect_distance_km=case.get('expect_distance_km'),
            destination_needle=case.get('destination_needle', ''),
            min_total=int(case.get('min_total', 1)),
        )
        result.pass_ = ok
        result.detail = detail
        result.distance_km_seen = distance_km
        result.first_url = first_url
        result.first_title = first_title
        result.meta_scope = meta_scope
        return result

    if len(turns) < 2:
        result.detail = 'missing turns for conversational case'
        return result

    turn1_ok = _turn1_clarification_ok(turns[0])
    if not turn1_ok:
        result.detail = 'turn1: expected clarification before radius search'
        return result

    turn_spec = case['turns'][1]
    ok, detail, distance_km, first_url, first_title, meta_scope = _evaluate_search_turn(
        turns[1],
        expect_distance_km=turn_spec.get('expect_distance_km'),
        destination_needle=turn_spec.get('destination_needle', ''),
        min_total=int(turn_spec.get('min_total', 1)),
    )
    result.pass_ = ok
    result.detail = f'turn1=ok; turn2: {detail}'
    result.distance_km_seen = distance_km
    result.first_url = first_url
    result.first_title = first_title
    result.meta_scope = meta_scope
    return result


def _check_health(base: str) -> str | None:
    url = f"{base.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            if resp.status != 200:
                return f'GET /health -> HTTP {resp.status}'
    except Exception as exc:  # noqa: BLE001
        return f'servidor no accessible: {exc}'
    return None


def _format_totals(totals: dict[str, int]) -> str:
    if not totals:
        return '(cap)'
    return ', '.join(f'{tool}={total}' for tool, total in totals.items())


def _collect_case_totals(turns: list[TurnResult]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for turn in turns:
        merged.update(turn.tool_totals)
    return merged


def _collect_tools(turns: list[TurnResult]) -> list[str]:
    tools: list[str] = []
    for turn in turns:
        tools.extend(turn.tools_called)
    return tools


def main() -> int:
    _load_env()

    if not mysql_available():
        print(
            'SKIP: MYSQL_* / AGENT_MYSQL_* no configurat — '
            'uat_experiences_radius requereix MySQL staging.',
        )
        return 0

    health_error = _check_health(BASE)
    if health_error:
        print(f'ERROR: {health_error}')
        print(f"Assegura't que el servidor respon a {BASE}")
        return 1

    lines: list[str] = []
    header = f'UAT radi experiències (#44) — base={BASE}\n'
    print(header, end='')
    lines.append(header)

    results: list[CaseResult] = []
    for index, case in enumerate(CASES, 1):
        line_start = f"[{index}/{len(CASES)}] {case['id']}: {case['description']}"
        print(line_start)
        lines.append(line_start)

        session_id = str(uuid.uuid4())
        turns: list[TurnResult] = []
        for turn_spec in case['turns']:
            print(f"  user: {turn_spec['message']}")
            lines.append(f"  user: {turn_spec['message']}")
            turn = run_turn(turn_spec['message'], session_id, BASE)
            turns.append(turn)
            if turn.error:
                print(f'  ERROR turn: {turn.error}')
                lines.append(f'  ERROR turn: {turn.error}')
                break

        evaluated = evaluate_case(case, turns)
        results.append(evaluated)

        tools_str = ', '.join(_collect_tools(turns)) or '(cap)'
        totals = _collect_case_totals(turns)
        status = 'PASS' if evaluated.pass_ else 'FAIL'
        detail = (
            f"  -> {status} | tools={tools_str} | distance_km={evaluated.distance_km_seen} | "
            f"totals={_format_totals(totals)} | meta.scope={evaluated.meta_scope or '—'} | "
            f"url={evaluated.first_url or '—'}"
        )
        print(detail)
        lines.append(detail)
        if evaluated.first_title:
            title_line = f'  title={evaluated.first_title}'
            print(title_line)
            lines.append(title_line)
        if not evaluated.pass_:
            fail_line = f'  detail: {evaluated.detail}'
            print(fail_line)
            lines.append(fail_line)
        print()
        lines.append('')

    passed = sum(1 for result in results if result.pass_)
    total = len(results) or 1
    pct = round(100 * passed / total)
    summary = [
        '=' * 60,
        f'RESULTAT: {passed}/{total} PASS | umbral 100% -> '
        f"{'OK' if passed == total else 'KO'} ({pct}%)",
        '=' * 60,
    ]
    for row in summary:
        print(row)
        lines.append(row)
    for result in results:
        mark = 'OK' if result.pass_ else 'KO'
        row = (
            f'  [{mark}] {result.case_id} distance_km={result.distance_km_seen} '
            f'url={result.first_url or "—"}'
        )
        print(row)
        lines.append(row)

    RESULTS_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\nResultats guardats a {RESULTS_PATH}')
    return 0 if passed == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
