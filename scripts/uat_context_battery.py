"""DEV-605 / CA-07 — UAT context conversacional multi-turn contra /api/chat."""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5010"
RESULTS_PATH = Path(__file__).resolve().parent / "uat_context_battery_results.txt"

SCENARIOS: list[dict] = [
    {
        "id": "UAT-CTX-01",
        "description": "Berguedà → dormir allà (establishments + destination)",
        "turns": [
            {"message": "Vull anar al Berguedà aquest cap de setmana."},
            {
                "message": "On puc dormir allà?",
                "evaluate": {
                    "expected_tool": "search_establishments",
                    "destination_contains": ["bergued"],
                },
            },
        ],
    },
    {
        "id": "UAT-CTX-02",
        "description": "Vall d'Aran → rutes fàcils (routes + aran)",
        "turns": [
            {"message": "Vull passar el cap de setmana a la Vall d'Aran."},
            {
                "message": "Hi ha rutes fàcils?",
                "evaluate": {
                    "expected_tool": "search_routes",
                    "destination_contains": ["aran"],
                },
            },
        ],
    },
    {
        "id": "UAT-CTX-03",
        "description": "Besalú → dormir allà (establishments + besalu)",
        "turns": [
            {"message": "Què veure a Besalú?"},
            {
                "message": "I on dormir allà?",
                "evaluate": {
                    "expected_tool": "search_establishments",
                    "destination_contains": ["besalu"],
                },
            },
        ],
    },
    {
        "id": "UAT-CTX-04",
        "description": "ES: Empordà → dormir allí (lang=es + empord)",
        "turns": [
            {"message": "Quiero ir al Empordà este fin de semana."},
            {
                "message": "¿Dónde puedo dormir allí?",
                "evaluate": {
                    "expected_tool": "search_establishments",
                    "destination_contains": ["empord"],
                    "expected_lang": "es",
                },
            },
        ],
    },
    {
        "id": "UAT-CTX-05",
        "description": "Reset: després de session/reset no hereta Berguedà",
        "turns": [
            {"message": "Vull anar al Berguedà."},
            {"reset": True},
            {
                "message": "On puc dormir?",
                "evaluate": {
                    "reset_no_destination": ["bergued"],
                },
            },
        ],
    },
]


@dataclass
class TurnResult:
    message: str
    http_ok: bool = False
    done: bool = False
    tools_called: list[str] = field(default_factory=list)
    tool_inputs: dict[str, dict] = field(default_factory=dict)
    text: str = ""
    error: str | None = None


@dataclass
class ScenarioResult:
    scenario_id: str
    description: str
    turns: list[TurnResult] = field(default_factory=list)
    context_ok: bool = False
    error: str | None = None

    @property
    def pass_(self) -> bool:
        return (
            self.error is None
            and self.context_ok
            and all(t.http_ok and t.done and t.error is None for t in self.turns)
        )


def _normalize(text: str) -> str:
    lowered = (text or "").lower().strip()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _destination_ok(tool_input: dict | None, needles: list[str]) -> bool:
    if not tool_input:
        return False
    destination = _normalize(str(tool_input.get("destination", "")))
    return any(needle in destination for needle in needles)


def _post_json(url: str, payload: dict, timeout: int = 180) -> tuple[int, str | None]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def run_turn(message: str, session_id: str, base: str) -> TurnResult:
    url = f"{base.rstrip('/')}/api/chat"
    result = TurnResult(message=message)
    status, raw = _post_json(url, {"message": message, "session_id": session_id})
    if status != 200:
        result.error = f"HTTP {status}"
        result.http_ok = False
        return result

    result.http_ok = True
    buffer = raw or ""
    while "\n\n" in buffer:
        block, buffer = buffer.split("\n\n", 1)
        for line in block.split("\n"):
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                ev = json.loads(payload)
            except json.JSONDecodeError:
                continue
            t = ev.get("type")
            if t == "tool_call":
                tool = ev.get("tool", "")
                result.tools_called.append(tool)
                inp = ev.get("input")
                if isinstance(inp, dict):
                    result.tool_inputs[tool] = inp
            elif t == "text_chunk":
                result.text += ev.get("content", ev.get("text", ""))
            elif t == "done":
                result.done = True
                result.text = result.text or ev.get("full_text", "")
            elif t == "error":
                result.error = ev.get("message")

    result.text = result.text.strip()
    return result


def reset_session(session_id: str, base: str) -> bool:
    url = f"{base.rstrip('/')}/api/session/reset"
    status, _ = _post_json(url, {"session_id": session_id}, timeout=30)
    return status == 200


def _evaluate_turn(turn_spec: dict, turn_result: TurnResult) -> tuple[bool, str]:
    ev = turn_spec.get("evaluate")
    if not ev:
        return True, "setup turn"

    if ev.get("reset_no_destination"):
        forbidden = ev["reset_no_destination"]
        for tool, inp in turn_result.tool_inputs.items():
            dest = _normalize(str((inp or {}).get("destination", "")))
            if any(f in dest for f in forbidden):
                return False, f"reset inherited destination in {tool}: {inp.get('destination')}"
        if turn_result.tools_called:
            return True, "tool without forbidden destination"
        clarify = (
            r"\bquin(a|e)\b",
            r"\bcomarca\b",
            r"\bzona\b",
            r"\bwhere\b",
            r"\bdónde\b",
            r"\bconcret",
        )
        if any(re.search(p, _normalize(turn_result.text)) for p in clarify):
            return True, "asks clarification (no tool)"
        return True, "no catalog tool with inherited destination"

    expected_tool = ev.get("expected_tool")
    if expected_tool and expected_tool not in turn_result.tools_called:
        return False, f"expected tool {expected_tool}, got {turn_result.tools_called}"

    needles = ev.get("destination_contains", [])
    if needles:
        inp = turn_result.tool_inputs.get(expected_tool, {})
        if not _destination_ok(inp, needles):
            return False, f"destination mismatch: {inp.get('destination')!r} not in {needles}"

    expected_lang = ev.get("expected_lang")
    if expected_lang:
        inp = turn_result.tool_inputs.get(expected_tool, {})
        lang = str(inp.get("lang", "")).strip()
        if lang != expected_lang:
            return False, f"expected lang={expected_lang}, got {lang!r}"

    return True, "ok"


def evaluate_scenario(scenario: dict, turns: list[TurnResult]) -> ScenarioResult:
    out = ScenarioResult(
        scenario_id=scenario["id"],
        description=scenario["description"],
        turns=turns,
    )
    turn_idx = 0
    for turn_spec in scenario["turns"]:
        if turn_spec.get("reset"):
            continue
        if turn_idx >= len(turns):
            out.error = "missing turn result"
            return out
        turn_result = turns[turn_idx]
        turn_idx += 1

        if turn_result.error:
            out.error = turn_result.error
            return out
        if not (turn_result.http_ok and turn_result.done):
            out.error = "missing HTTP 200 or SSE done"
            return out
        if "evaluate" in turn_spec:
            ok, detail = _evaluate_turn(turn_spec, turn_result)
            out.context_ok = ok
            if not ok:
                out.error = detail
            return out

    out.context_ok = True
    return out


def run_scenario(scenario: dict, base: str) -> ScenarioResult:
    session_id = str(uuid.uuid4())
    turn_results: list[TurnResult] = []

    for turn_spec in scenario["turns"]:
        if turn_spec.get("reset"):
            if not reset_session(session_id, base):
                return ScenarioResult(
                    scenario_id=scenario["id"],
                    description=scenario["description"],
                    error="session reset failed",
                )
            continue
        tr = run_turn(turn_spec["message"], session_id, base)
        turn_results.append(tr)
        if tr.error or not tr.done:
            break
        time.sleep(0.3)

    return evaluate_scenario(scenario, turn_results)


def _write_results(lines: list[str]) -> None:
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    header = f"UAT context CA-07 — base={BASE}"
    print(header + "\n")
    output_lines = [header, ""]

    results: list[ScenarioResult] = []
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"[{i}/{len(SCENARIOS)}] {scenario['id']}: {scenario['description']}")
        ev = run_scenario(scenario, BASE)
        results.append(ev)
        status = "PASS" if ev.pass_ else "FAIL"
        print(f"  -> {status}")
        line = f"[{status}] {scenario['id']}: {scenario['description']}"
        output_lines.append(line)

        if ev.error:
            print(f"  ERROR: {ev.error}")
            output_lines.append(f"  ERROR: {ev.error}")
        for j, tr in enumerate(ev.turns, 1):
            tools = ", ".join(tr.tools_called) or "(cap)"
            dests = {
                t: (inp or {}).get("destination")
                for t, inp in tr.tool_inputs.items()
            }
            print(f"  turn {j}: {tr.message!r} | tools={tools} | dest={dests}")
            output_lines.append(
                f"  turn {j}: {tr.message!r} | tools={tools} | dest={dests}"
            )
        print()

    passed = sum(1 for r in results if r.pass_)
    pct = round(100 * passed / len(results))
    threshold_ok = passed >= 4
    summary = f"RESULTAT: {passed}/{len(results)} PASS ({pct}%) | Umbral >=80% (4/5): {'OK' if threshold_ok else 'KO'}"
    print("=" * 60)
    print(summary)
    print("=" * 60)
    output_lines.extend(["", summary])
    for r in results:
        mark = "OK" if r.pass_ else "KO"
        row = f"  [{mark}] {r.scenario_id}"
        print(row)
        output_lines.append(row)

    _write_results(output_lines)
    print(f"\nResults written to {RESULTS_PATH}")
    return 0 if threshold_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
