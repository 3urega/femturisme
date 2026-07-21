"""DEV-604 — UAT catàleg: 12 proves (2 per domini) contra /api/chat."""
from __future__ import annotations

import json
import sys
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5010"

CASES: list[dict] = [
    {
        "id": "UAT-EST-01",
        "domain": "establishments",
        "message": "On puc allotjar-me al Pirineu? Busco turisme rural.",
        "expected_tool": "search_establishments",
        "min_total": 1,
    },
    {
        "id": "UAT-EST-02",
        "domain": "establishments",
        "message": "Restaurants amb cuina catalana tradicional al Berguedà",
        "expected_tool": "search_establishments",
        "min_total": 0,
    },
    {
        "id": "UAT-ART-01",
        "domain": "articles",
        "message": "Articles sobre el Parc Natural del Cadí",
        "expected_tool": "search_articles",
        "min_total": 0,
    },
    {
        "id": "UAT-ART-02",
        "domain": "articles",
        "message": "Notícies sobre enoturisme a Catalunya",
        "expected_tool": "search_articles",
        "min_total": 0,
    },
    {
        "id": "UAT-DST-01",
        "domain": "destinations",
        "message": "Què veure a Besalú?",
        "expected_tool": "search_destinations",
        "min_total": 0,
    },
    {
        "id": "UAT-DST-02",
        "domain": "destinations",
        "message": "Destinacions per descobrir a l'Empordà",
        "expected_tool": "search_destinations",
        "min_total": 0,
    },
    {
        "id": "UAT-RTE-01",
        "domain": "routes",
        "message": "Rutes a peu a l'Empordà",
        "expected_tool": "search_routes",
        "min_total": 1,
    },
    {
        "id": "UAT-RTE-02",
        "domain": "routes",
        "message": "Rutes de senderisme al Pirineu",
        "expected_tool": "search_routes",
        "min_total": 0,
    },
    {
        "id": "UAT-EVT-01",
        "domain": "events",
        "message": "Què fer aquest cap de setmana a l'Empordà?",
        "expected_tool": "search_events",
        "min_total": 0,
        "forbidden_tools": ["search_experiences"],
    },
    {
        "id": "UAT-EVT-02",
        "domain": "events",
        "message": "Agenda d'esdeveniments a Catalunya aquest mes",
        "expected_tool": "search_events",
        "min_total": 0,
        "forbidden_tools": ["search_experiences"],
    },
    {
        "id": "UAT-EXP-01",
        "domain": "experiences",
        "message": "Quines experiències a la Costa Brava?",
        "expected_tool": "search_experiences",
        "min_total": 1,
        "forbidden_tools": ["search_events"],
    },
    {
        "id": "UAT-EXP-02",
        "domain": "experiences",
        "message": "Experiències de natura a la Garrotxa",
        "expected_tool": "search_experiences",
        "min_total": 0,
        "forbidden_tools": ["search_events"],
    },
    {
        "id": "UAT-EXP-03",
        "domain": "experiences",
        "message": "Visitas guiadas a 50 km de Calella",
        "expected_tool": "search_experiences",
        "min_total": 1,
        "forbidden_tools": ["search_events", "search_destinations"],
    },
]


@dataclass
class CaseResult:
    case_id: str
    domain: str
    message: str
    expected_tool: str
    tools_called: list[str] = field(default_factory=list)
    tool_totals: dict[str, int | None] = field(default_factory=dict)
    text: str = ""
    error: str | None = None
    routing_ok: bool = False
    total_ok: bool = False
    links_ok: bool = False
    forbidden_ok: bool = True

    @property
    def pass_(self) -> bool:
        return (
            self.error is None
            and self.routing_ok
            and self.total_ok
            and self.forbidden_ok
            and (self.links_ok or not self.tool_totals.get(self.expected_tool))
        )


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
    totals: dict[str, int | None] = {}
    text = ""
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
                        elif t == "tool_result":
                            tool = ev.get("tool", "")
                            res = ev.get("result", {})
                            total_raw = res.get("total") if isinstance(res, dict) else None
                            try:
                                total = int(total_raw) if total_raw is not None else None
                            except (TypeError, ValueError):
                                total = None
                            totals[tool] = total
                        elif t == "text_chunk":
                            text += ev.get("content", ev.get("text", ""))
                        elif t == "error":
                            return CaseResult(
                                case_id="",
                                domain="",
                                message=message,
                                expected_tool="",
                                error=ev.get("message"),
                            )
    except urllib.error.HTTPError as exc:
        return CaseResult(
            case_id="",
            domain="",
            message=message,
            expected_tool="",
            error=f"HTTP {exc.code}",
        )
    except Exception as exc:  # noqa: BLE001
        return CaseResult(
            case_id="",
            domain="",
            message=message,
            expected_tool="",
            error=str(exc),
        )

    return CaseResult(
        case_id="",
        domain="",
        message=message,
        expected_tool="",
        tools_called=tools,
        tool_totals=totals,
        text=text.strip(),
    )


def evaluate(case: dict, result: CaseResult) -> CaseResult:
    result.case_id = case["id"]
    result.domain = case["domain"]
    result.expected_tool = case["expected_tool"]
    result.routing_ok = case["expected_tool"] in result.tools_called
    total = result.tool_totals.get(case["expected_tool"])
    min_total = case.get("min_total", 0)
    if total is None and result.routing_ok:
        result.total_ok = min_total == 0
    elif total is not None:
        result.total_ok = total >= min_total
    else:
        result.total_ok = min_total == 0
    result.links_ok = "femturisme.cat" in result.text
    forbidden = case.get("forbidden_tools", [])
    result.forbidden_ok = not any(t in result.tools_called for t in forbidden)
    return result


def main() -> int:
    print(f"UAT catàleg DEV-604 — base={BASE}\n")
    results: list[CaseResult] = []
    for i, case in enumerate(CASES, 1):
        print(f"[{i}/12] {case['id']}: {case['message']}")
        raw = run_chat(case["message"], BASE)
        ev = evaluate(case, raw)
        results.append(ev)
        status = "PASS" if ev.pass_ else "FAIL"
        tools_str = ", ".join(ev.tools_called) or "(cap)"
        total = ev.tool_totals.get(case["expected_tool"], "—")
        print(f"  -> {status} | tools={tools_str} | total={total} | links={ev.links_ok}")
        if ev.error:
            print(f"  ERROR: {ev.error}")
        if not ev.routing_ok:
            print(f"  routing: esperat {case['expected_tool']}")
        if not ev.forbidden_ok:
            print(f"  forbidden: {case.get('forbidden_tools')}")
        print()

    passed = sum(1 for r in results if r.pass_)
    routing = sum(1 for r in results if r.routing_ok)
    pct = round(100 * routing / len(results))
    print("=" * 60)
    print(f"RESULTAT: {passed}/{len(results)} PASS complet | routing {routing}/{len(results)} ({pct}%)")
    print(f"Umbral DEV-604: >=80% routing -> {'OK' if pct >= 80 else 'KO'}")
    print("=" * 60)
    for r in results:
        mark = "OK" if r.pass_ else "KO"
        print(f"  [{mark}] {r.case_id} ({r.domain}) -> {r.tools_called}")
    return 0 if pct >= 80 and passed >= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
