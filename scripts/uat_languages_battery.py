"""DEV-601 — UAT idiomes ca/es/en/fr (RF-10) contra /api/chat."""
from __future__ import annotations

import json
import re
import sys
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from app.services.user_language import detect_user_language, foreign_language_markers

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5010"

CASES: list[dict] = [
    {
        "id": "UAT-LANG-CA-01",
        "lang": "ca",
        "message": "Quines rutes hi ha a l'Empordà?",
        "expected_tool": "search_routes",
    },
    {
        "id": "UAT-LANG-CA-02",
        "lang": "ca",
        "message": "On puc allotjar-me al Pirineu?",
        "expected_tool": "search_establishments",
    },
    {
        "id": "UAT-LANG-ES-01",
        "lang": "es",
        "message": "¿Qué rutas hay en el Empordà?",
        "expected_tool": "search_routes",
    },
    {
        "id": "UAT-LANG-ES-02",
        "lang": "es",
        "message": "¿Dónde puedo alojarme en el Pirineo?",
        "expected_tool": "search_establishments",
    },
    {
        "id": "UAT-LANG-EN-01",
        "lang": "en",
        "message": "What routes are there in Empordà?",
        "expected_tool": "search_routes",
    },
    {
        "id": "UAT-LANG-EN-02",
        "lang": "en",
        "message": "Where can I stay in the Pyrenees?",
        "expected_tool": "search_establishments",
    },
    {
        "id": "UAT-LANG-FR-01",
        "lang": "fr",
        "message": "Quelles randonnées y a-t-il en Catalogne?",
        "expected_tool": "search_routes",
    },
    {
        "id": "UAT-LANG-FR-02",
        "lang": "fr",
        "message": "Où puis-je dormir dans les Pyrénées?",
        "expected_tool": "search_establishments",
    },
]

_CA_FORBIDDEN = (r'\bdime\b', r'\btienes\b', r'\bquieres\b', r'\bhay\b', r'¿')
_ES_FORBIDDEN = (r'\bquins?\b', r'\bquè\b', r"\bl'", r'\ballotjar')


@dataclass
class CaseResult:
    case_id: str
    lang: str
    message: str
    expected_tool: str
    tools_called: list[str] = field(default_factory=list)
    tool_langs: dict[str, str] = field(default_factory=dict)
    text: str = ""
    done: bool = False
    error: str | None = None
    detect_ok: bool = False
    routing_ok: bool = False
    lang_inject_ok: bool = False
    reply_lang_ok: bool = False

    @property
    def pass_(self) -> bool:
        return (
            self.error is None
            and self.done
            and self.detect_ok
            and self.routing_ok
            and self.lang_inject_ok
            and self.reply_lang_ok
        )


def _foreign_marker_hits(text: str, lang: str) -> int:
    markers = foreign_language_markers(lang)  # type: ignore[arg-type]
    lowered = (text or '').lower()
    return sum(1 for pattern in markers if re.search(pattern, lowered))


def _reply_language_ok(lang: str, text: str) -> bool:
    if not text.strip():
        return False
    lowered = text.lower()
    if lang == 'ca':
        if any(re.search(p, lowered) for p in _CA_FORBIDDEN):
            return False
        return _foreign_marker_hits(text, 'ca') <= 2
    if lang == 'es':
        if any(re.search(p, lowered) for p in _ES_FORBIDDEN):
            return False
        return _foreign_marker_hits(text, 'es') <= 2
    if lang == 'en':
        en_hits = sum(
            1
            for p in (r'\bthe\b', r'\band\b', r'\byou\b', r'\broute', r'\bhotel', r'\bthere\b')
            if re.search(p, lowered)
        )
        return en_hits >= 1 and _foreign_marker_hits(text, 'en') <= 3
    if lang == 'fr':
        fr_hits = sum(
            1
            for p in (r'\bles\b', r'\bdes\b', r'\bpour\b', r'\bvous\b', r'\broute', r'\bhôtel')
            if re.search(p, lowered)
        )
        return fr_hits >= 1 and _foreign_marker_hits(text, 'fr') <= 3
    return True


def run_chat(message: str, base: str) -> CaseResult:
    url = f"{base.rstrip('/')}/api/chat"
    body = json.dumps({"message": message, "session_id": str(uuid.uuid4())}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    tools: list[str] = []
    tool_langs: dict[str, str] = {}
    text = ""
    done = False
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            buffer = ""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    for line in block.split("\n"):
                        if not line.startswith("data: "):
                            continue
                        raw = line[6:].strip()
                        if not raw or raw == "[DONE]":
                            continue
                        try:
                            ev = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        t = ev.get("type")
                        if t == "tool_call":
                            tool = ev.get("tool", "")
                            tools.append(tool)
                            inp = ev.get("input") or {}
                            if isinstance(inp, dict) and inp.get("lang"):
                                tool_langs[tool] = str(inp["lang"])
                        elif t == "text_chunk":
                            text += ev.get("content", ev.get("text", ""))
                        elif t == "done":
                            done = True
                            text = text or ev.get("full_text", "")
                        elif t == "error":
                            return CaseResult(
                                case_id="",
                                lang="",
                                message=message,
                                expected_tool="",
                                error=ev.get("message"),
                            )
    except urllib.error.HTTPError as exc:
        return CaseResult(
            case_id="",
            lang="",
            message=message,
            expected_tool="",
            error=f"HTTP {exc.code}",
        )
    except Exception as exc:  # noqa: BLE001
        return CaseResult(
            case_id="",
            lang="",
            message=message,
            expected_tool="",
            error=str(exc),
        )

    return CaseResult(
        case_id="",
        lang="",
        message=message,
        expected_tool="",
        tools_called=tools,
        tool_langs=tool_langs,
        text=text.strip(),
        done=done,
    )


def evaluate(case: dict, result: CaseResult) -> CaseResult:
    result.case_id = case["id"]
    result.lang = case["lang"]
    result.expected_tool = case["expected_tool"]
    result.detect_ok = detect_user_language(case["message"]) == case["lang"]
    result.routing_ok = case["expected_tool"] in result.tools_called
    injected = result.tool_langs.get(case["expected_tool"])
    result.lang_inject_ok = injected == case["lang"]
    result.reply_lang_ok = _reply_language_ok(case["lang"], result.text)
    return result


def main() -> int:
    print(f"UAT idiomes DEV-601 — base={BASE}\n")
    results: list[CaseResult] = []
    for i, case in enumerate(CASES, 1):
        print(f"[{i}/8] {case['id']}: {case['message']}")
        raw = run_chat(case["message"], BASE)
        ev = evaluate(case, raw)
        results.append(ev)
        status = "PASS" if ev.pass_ else "FAIL"
        lang_val = ev.tool_langs.get(case["expected_tool"], "—")
        print(f"  -> {status} | tool={case['expected_tool']} | lang={lang_val} | done={ev.done}")
        if ev.error:
            print(f"  ERROR: {ev.error}")
        if not ev.detect_ok:
            print(f"  detect: esperat {case['lang']}")
        if not ev.routing_ok:
            print(f"  routing: esperat {case['expected_tool']} en {ev.tools_called}")
        if not ev.lang_inject_ok:
            print(f"  lang inject: esperat {case['lang']}, obtingut {lang_val}")
        if not ev.reply_lang_ok:
            preview = (ev.text[:120] + "…") if len(ev.text) > 120 else ev.text
            print(f"  reply lang: KO | {preview!r}")
        print()

    passed = sum(1 for r in results if r.pass_)
    pct = round(100 * passed / len(results))
    print("=" * 60)
    print(f"RESULTAT: {passed}/{len(results)} PASS ({pct}%)")
    print(f"Umbral DEV-601: >=80% (6/8) -> {'OK' if passed >= 6 else 'KO'}")
    print("=" * 60)
    for r in results:
        mark = "OK" if r.pass_ else "KO"
        print(f"  [{mark}] {r.case_id} ({r.lang})")
    return 0 if passed >= 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
