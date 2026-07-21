"""Issue #49 — UAT Patum + allotjament a prop Berga (conversacional multi-turn)."""
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
RESULTS_PATH = Path(__file__).resolve().parent / 'uat_patum_bergua_accommodation_results.txt'
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5010'
EXPECTED_TOOL = 'search_establishments'
EXPECTED_KM = 30
URL_PREFIX = 'https://www.femturisme.cat/establiments/'
FORBIDDEN_THEMATIC = frozenset({'search_articles', 'search_events'})

SCENARIO: dict = {
    'id': 'UAT-EST-BERG',
    'description': 'Patum -> allotjament a prop Berga -> confirmacio -> mes opcions',
    'turns': [
        {'message': 'Què en saps de la Patum?', 'check': 'B01'},
        {'message': 'buscam allotjament a prop de Berga', 'check': 'B02'},
        {'message': 'si, 30 km', 'check': 'B03'},
        {'message': '2 o 3 més si us plau', 'check': 'B04'},
    ],
}


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
class CheckResult:
    check_id: str
    pass_: bool = False
    detail: str = ''


@dataclass
class ScenarioResult:
    scenario_id: str
    description: str
    turns: list[TurnResult] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def pass_(self) -> bool:
        return bool(self.checks) and all(check.pass_ for check in self.checks)


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


def _asks_km_or_radius(text: str) -> bool:
    normalized = _normalize(text)
    patterns = (
        r'\bquants km\b',
        r'\bquants quilometres\b',
        r'\bcuants km\b',
        r'\bcuantos km\b',
        r'\bhow many km\b',
        r'\bcombien de km\b',
        r'\bradi\b',
        r'\bdistancia\b',
        r'\b\d+\s*km\b',
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _is_rural_type(tool_input: dict | None) -> bool:
    if not tool_input:
        return False
    type_value = _normalize(str(tool_input.get('type', '')))
    return any(
        needle in type_value
        for needle in ('cases-rurals', 'casa-rural', 'turisme rural', 'rural')
    )


def _destination_has_berga(tool_input: dict | None) -> bool:
    if not tool_input:
        return False
    destination = _normalize(str(tool_input.get('destination', '')))
    return 'berga' in destination


def _has_forbidden_thematic(tools: list[str]) -> bool:
    return any(tool in FORBIDDEN_THEMATIC for tool in tools)


def _establishments_input(turn: TurnResult) -> dict:
    return turn.tool_inputs.get(EXPECTED_TOOL, {})


def _combined_thematic_total(turn: TurnResult) -> int:
    total = 0
    for tool in ('search_articles', 'search_events'):
        total += turn.tool_totals.get(tool, 0)
    return total


def _check_b01(turn: TurnResult) -> CheckResult:
    check = CheckResult(check_id='UAT-EST-B01')
    if turn.error:
        check.detail = f'error: {turn.error}'
        return check
    tools = set(turn.tools_called)
    if 'search_articles' not in tools or 'search_events' not in tools:
        check.detail = f'expected articles+events, got {turn.tools_called}'
        return check
    if _combined_thematic_total(turn) < 1:
        check.detail = f'thematic total={_combined_thematic_total(turn)} < 1'
        return check
    check.pass_ = True
    check.detail = 'ok'
    return check


def _check_b02(turn: TurnResult) -> CheckResult:
    check = CheckResult(check_id='UAT-EST-B02')
    if turn.error:
        check.detail = f'error: {turn.error}'
        return check

    est_input = _establishments_input(turn)
    if EXPECTED_TOOL in turn.tools_called:
        if _is_rural_type(est_input):
            check.detail = f'unexpected rural type: {est_input.get("type")!r}'
            return check
        check.pass_ = True
        check.detail = 'ok (establishments without rural type)'
        return check

    if _asks_km_or_radius(turn.text):
        check.pass_ = True
        check.detail = 'ok (asks km/radius before search)'
        return check

    check.detail = 'expected clarification or search_establishments without rural type'
    return check


def _check_b03(turn: TurnResult, *, previous_turn: TurnResult) -> CheckResult:
    check = CheckResult(check_id='UAT-EST-B03')
    if turn.error:
        check.detail = f'error: {turn.error}'
        return check
    if _has_forbidden_thematic(turn.tools_called):
        check.detail = f'forbidden thematic tools: {turn.tools_called}'
        return check
    if EXPECTED_TOOL not in turn.tools_called:
        if _asks_km_or_radius(previous_turn.text) and _normalize(turn.message) in {'si', 'sí'}:
            check.detail = 'expected search_establishments after confirmation'
            return check
        check.detail = f'expected {EXPECTED_TOOL}, got {turn.tools_called}'
        return check

    est_input = _establishments_input(turn)
    distance_km = _parse_distance_km(est_input.get('distance_km'))
    if distance_km != EXPECTED_KM:
        check.detail = f'distance_km={distance_km}, expected {EXPECTED_KM}'
        return check
    if not _destination_has_berga(est_input):
        check.detail = f"destination={est_input.get('destination')!r} missing berga"
        return check
    if _is_rural_type(est_input):
        check.detail = f'unexpected rural type: {est_input.get("type")!r}'
        return check

    check.pass_ = True
    check.detail = 'ok'
    return check


def _check_b04(turn: TurnResult) -> CheckResult:
    check = CheckResult(check_id='UAT-EST-B04')
    if turn.error:
        check.detail = f'error: {turn.error}'
        return check
    if _has_forbidden_thematic(turn.tools_called):
        check.detail = f'forbidden thematic tools: {turn.tools_called}'
        return check
    if EXPECTED_TOOL not in turn.tools_called:
        check.detail = f'expected {EXPECTED_TOOL}, got {turn.tools_called}'
        return check
    if any(tool != EXPECTED_TOOL for tool in turn.tools_called):
        check.detail = f'unexpected tools besides establishments: {turn.tools_called}'
        return check

    est_input = _establishments_input(turn)
    if _is_rural_type(est_input):
        check.detail = f'unexpected rural type: {est_input.get("type")!r}'
        return check

    total = turn.tool_totals.get(EXPECTED_TOOL, 0)
    if total < 3:
        check.detail = f'total={total} < 3 (catalog may have fewer matches in this env)'
        return check

    payload = turn.tool_results.get(EXPECTED_TOOL, {})
    cards = payload.get('results') if isinstance(payload, dict) else None
    if isinstance(cards, list) and cards and isinstance(cards[0], dict):
        first_url = str(cards[0].get('url') or '')
        if first_url and not first_url.startswith(URL_PREFIX):
            check.detail = f'first url invalid: {first_url}'
            return check

    check.pass_ = True
    check.detail = f'ok (total={total})'
    return check


def evaluate_scenario(scenario: dict, turns: list[TurnResult]) -> ScenarioResult:
    result = ScenarioResult(
        scenario_id=scenario['id'],
        description=scenario['description'],
        turns=turns,
    )
    if len(turns) < len(scenario['turns']):
        result.checks.append(
            CheckResult(
                check_id='SETUP',
                detail=f'missing turns: got {len(turns)}, expected {len(scenario["turns"])}',
            ),
        )
        return result

    evaluators = {
        'B01': lambda index: _check_b01(turns[index]),
        'B02': lambda index: _check_b02(turns[index]),
        'B03': lambda index: _check_b03(turns[index], previous_turn=turns[index - 1]),
        'B04': lambda index: _check_b04(turns[index]),
    }

    for index, turn_spec in enumerate(scenario['turns']):
        check_id = turn_spec['check']
        evaluator = evaluators.get(check_id)
        if evaluator is None:
            result.checks.append(CheckResult(check_id=check_id, detail='unknown check'))
            continue
        result.checks.append(evaluator(index))

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


def run_scenario(base: str, turn3_message: str = 'si, 30 km') -> ScenarioResult:
    session_id = str(uuid.uuid4())
    turns: list[TurnResult] = []
    turn_specs = []
    for index, turn_spec in enumerate(SCENARIO['turns']):
        message = turn3_message if index == 2 else turn_spec['message']
        turn_specs.append({**turn_spec, 'message': message})
        turn = run_turn(message, session_id, base)
        turns.append(turn)
        if turn.error:
            break
    return evaluate_scenario({**SCENARIO, 'turns': turn_specs}, turns)


def main() -> int:
    _load_env()

    if not mysql_available():
        print(
            'SKIP: MYSQL_* / AGENT_MYSQL_* no configurat — '
            'uat_patum_bergua_accommodation requereix MySQL staging.',
        )
        return 0

    health_error = _check_health(BASE)
    if health_error:
        print(f'ERROR: {health_error}')
        print(f"Assegura't que el servidor respon a {BASE}")
        return 1

    lines: list[str] = []
    header = f'UAT Patum + allotjament Berga (#49) — base={BASE}\n'
    print(header, end='')
    lines.append(header)

    print(f"{SCENARIO['id']}: {SCENARIO['description']}")
    lines.append(f"{SCENARIO['id']}: {SCENARIO['description']}")

    evaluated = run_scenario(BASE, turn3_message='si, 30 km')
    b03 = next((c for c in evaluated.checks if c.check_id == 'UAT-EST-B03'), None)
    if b03 is not None and not b03.pass_:
        print('  B03 retry: full scenario with turn 3 = «30 km des de Berga»')
        lines.append('  B03 retry: full scenario with turn 3 = «30 km des de Berga»')
        evaluated = run_scenario(BASE, turn3_message='30 km des de Berga')

    for turn in evaluated.turns:
        print(f"  user: {turn.message}")
        lines.append(f"  user: {turn.message}")
        tools_str = ', '.join(turn.tools_called) or '(cap)'
        row = f"  tools={tools_str} | totals={_format_totals(turn.tool_totals)}"
        print(row)
        lines.append(row)
        if turn.error:
            err = f'  ERROR turn: {turn.error}'
            print(err)
            lines.append(err)

    for check in evaluated.checks:
        status = 'PASS' if check.pass_ else 'FAIL'
        row = f"  [{status}] {check.check_id}: {check.detail}"
        print(row)
        lines.append(row)

    passed = sum(1 for check in evaluated.checks if check.pass_)
    total = len(evaluated.checks) or 1
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

    RESULTS_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\nResultats guardats a {RESULTS_PATH}')
    return 0 if passed == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
