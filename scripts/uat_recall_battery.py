"""Issue #40 — UAT recall catàleg: golden queries temàtiques amb total >= 1."""
from __future__ import annotations

import json
import os
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
RESULTS_PATH = Path(__file__).resolve().parent / 'uat_recall_battery_results.txt'
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5010'
PASS_THRESHOLD_PCT = 80

CASES: list[dict] = [
    {
        'id': 'UAT-REC-01',
        'theme': 'patum',
        'message': 'Què és la Patum?',
        'keywords': ['patum'],
        'min_total': 1,
    },
    {
        'id': 'UAT-REC-02',
        'theme': 'fira_pals',
        'message': 'Quan és la Fira medieval de Pals?',
        'keywords': ['fira', 'medieval'],
        'min_total': 1,
    },
    {
        'id': 'UAT-REC-03',
        'theme': 'castellers',
        'message': 'Articles sobre castellers a Barcelona',
        'keywords': ['casteller'],
        'min_total': 1,
    },
    {
        'id': 'UAT-REC-04',
        'theme': 'parc_cadi',
        'message': 'Articles sobre el Parc Natural del Cadí',
        'keywords': ['cadi', 'cadí', 'parc', 'moixeró'],
        'min_total': 1,
    },
    {
        'id': 'UAT-REC-05',
        'theme': 'enoturisme',
        'message': 'Notícies sobre enoturisme a Catalunya',
        'keywords': ['enoturisme'],
        'min_total': 1,
    },
]


@dataclass
class CaseResult:
    case_id: str
    theme: str
    message: str
    tools_called: list[str] = field(default_factory=list)
    tool_totals: dict[str, int] = field(default_factory=dict)
    tool_results: dict[str, dict] = field(default_factory=dict)
    first_url: str | None = None
    first_title: str | None = None
    recall_ok: bool = False
    links_ok: bool = False
    keywords_ok: bool = False
    skipped: bool = False
    skip_reason: str | None = None
    error: str | None = None

    @property
    def pass_(self) -> bool:
        return (
            not self.skipped
            and self.error is None
            and self.recall_ok
            and self.links_ok
            and self.keywords_ok
        )


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


def _parse_total(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def run_chat(message: str, base: str) -> CaseResult:
    url = f"{base.rstrip('/')}/api/chat"
    body = json.dumps({'message': message, 'session_id': str(uuid.uuid4())}).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    tools: list[str] = []
    totals: dict[str, int] = {}
    results_by_tool: dict[str, dict] = {}

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            buffer = ''
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='replace')
                while '\n\n' in buffer:
                    block, buffer = buffer.split('\n\n', 1)
                    for line in block.split('\n'):
                        if not line.startswith('data: '):
                            continue
                        raw = line[6:].strip()
                        if not raw or raw == '[DONE]':
                            continue
                        try:
                            ev = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        event_type = ev.get('type')
                        if event_type == 'tool_call':
                            tool = ev.get('tool', '')
                            if tool:
                                tools.append(tool)
                        elif event_type == 'tool_result':
                            tool = ev.get('tool', '')
                            res = ev.get('result', {})
                            if isinstance(res, dict):
                                total = _parse_total(res.get('total'))
                                if total is not None:
                                    totals[tool] = total
                                results_by_tool[tool] = res
                        elif event_type == 'error':
                            return CaseResult(
                                case_id='',
                                theme='',
                                message=message,
                                error=ev.get('message'),
                            )
    except urllib.error.HTTPError as exc:
        return CaseResult(
            case_id='',
            theme='',
            message=message,
            error=f'HTTP {exc.code}',
        )
    except Exception as exc:  # noqa: BLE001
        return CaseResult(
            case_id='',
            theme='',
            message=message,
            error=str(exc),
        )

    return CaseResult(
        case_id='',
        theme='',
        message=message,
        tools_called=tools,
        tool_totals=totals,
        tool_results=results_by_tool,
    )


def _find_recall_card(
    tool_totals: dict[str, int],
    tool_results: dict[str, dict],
    *,
    min_total: int,
    keywords: list[str],
) -> tuple[dict | None, str | None, int]:
    max_total = max(tool_totals.values()) if tool_totals else 0
    if max_total < min_total:
        return None, None, max_total

    for tool, total in sorted(tool_totals.items(), key=lambda item: item[1], reverse=True):
        if total < min_total:
            continue
        payload = tool_results.get(tool, {})
        cards = payload.get('results') if isinstance(payload, dict) else None
        if not isinstance(cards, list):
            continue
        for card in cards:
            if not isinstance(card, dict):
                continue
            if keywords and _keyword_match(card, keywords):
                return card, tool, total
        if not keywords and cards:
            first = cards[0] if isinstance(cards[0], dict) else None
            if first is not None:
                return first, tool, total

    for tool, total in sorted(tool_totals.items(), key=lambda item: item[1], reverse=True):
        if total < min_total:
            continue
        payload = tool_results.get(tool, {})
        cards = payload.get('results') if isinstance(payload, dict) else None
        if isinstance(cards, list) and cards and isinstance(cards[0], dict):
            return cards[0], tool, total

    return None, None, max_total


def _keyword_match(card: dict | None, keywords: list[str]) -> bool:
    if not card or not keywords:
        return False
    haystack = _normalize(
        ' '.join(
            str(card.get(field, '') or '')
            for field in ('title', 'url', 'description')
        ),
    )
    return any(_normalize(keyword) in haystack for keyword in keywords)


def evaluate(case: dict, raw: CaseResult) -> CaseResult:
    raw.case_id = case['id']
    raw.theme = case['theme']
    min_total = int(case.get('min_total', 1))
    keywords = list(case.get('keywords', []))

    max_total = max(raw.tool_totals.values()) if raw.tool_totals else 0
    raw.recall_ok = max_total >= min_total

    card, _matched_tool, _matched_total = _find_recall_card(
        raw.tool_totals,
        raw.tool_results,
        min_total=min_total,
        keywords=keywords,
    )
    if card:
        raw.first_url = str(card.get('url') or '') or None
        raw.first_title = str(card.get('title') or '') or None
        url = raw.first_url or ''
        raw.links_ok = url.startswith('https://www.femturisme.cat')
        raw.keywords_ok = _keyword_match(card, keywords) if keywords else True
    else:
        raw.links_ok = False
        raw.keywords_ok = False

    return raw


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


def main() -> int:
    _load_env()

    if not mysql_available():
        print(
            'SKIP: MYSQL_* / AGENT_MYSQL_* no configurat — '
            'uat_recall_battery requereix MySQL staging.',
        )
        return 0

    health_error = _check_health(BASE)
    if health_error:
        print(f'ERROR: {health_error}')
        print(f'Assegura\'t que el servidor respon a {BASE}')
        return 1

    lines: list[str] = []
    header = f'UAT recall catàleg (#40) — base={BASE}\n'
    print(header, end='')
    lines.append(header)

    results: list[CaseResult] = []
    for index, case in enumerate(CASES, 1):
        line_start = f"[{index}/{len(CASES)}] {case['id']} ({case['theme']}): {case['message']}"
        print(line_start)
        lines.append(line_start)

        raw = run_chat(case['message'], BASE)
        ev = evaluate(case, raw)
        results.append(ev)

        status = 'PASS' if ev.pass_ else 'FAIL'
        tools_str = ', '.join(ev.tools_called) or '(cap)'
        detail = (
            f"  -> {status} | tools={tools_str} | totals={_format_totals(ev.tool_totals)} | "
            f"url={ev.first_url or '—'}"
        )
        print(detail)
        lines.append(detail)
        if ev.first_title:
            title_line = f"  title={ev.first_title}"
            print(title_line)
            lines.append(title_line)
        if ev.error:
            err_line = f'  ERROR: {ev.error}'
            print(err_line)
            lines.append(err_line)
        if not ev.recall_ok:
            miss = f'  recall: max total {max(ev.tool_totals.values()) if ev.tool_totals else 0} < min_total {case["min_total"]}'
            print(miss)
            lines.append(miss)
        if ev.recall_ok and not ev.links_ok:
            print('  links: primera card sense URL femturisme.cat')
            lines.append('  links: primera card sense URL femturisme.cat')
        if ev.recall_ok and not ev.keywords_ok:
            print(f"  keywords: cap coincidència amb {case.get('keywords')}")
            lines.append(f"  keywords: cap coincidència amb {case.get('keywords')}")
        print()
        lines.append('')

    executed = [r for r in results if not r.skipped]
    passed = sum(1 for r in executed if r.pass_)
    total = len(executed) or 1
    pct = round(100 * passed / total)
    summary = [
        '=' * 60,
        f'RESULTAT: {passed}/{total} PASS | umbral >= {PASS_THRESHOLD_PCT}% -> '
        f"{'OK' if pct >= PASS_THRESHOLD_PCT else 'KO'} ({pct}%)",
        '=' * 60,
    ]
    for row in summary:
        print(row)
        lines.append(row)
    for result in results:
        mark = 'OK' if result.pass_ else 'KO'
        row = f'  [{mark}] {result.case_id} ({result.theme}) -> totals={_format_totals(result.tool_totals)}'
        print(row)
        lines.append(row)

    RESULTS_PATH.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'\nResultats guardats a {RESULTS_PATH}')

    return 0 if pct >= PASS_THRESHOLD_PCT else 1


if __name__ == '__main__':
    raise SystemExit(main())
