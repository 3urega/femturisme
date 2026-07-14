"""CA-04 smoke: pregunta composta → >=2 tools de catàleg (manual DEV-605)."""
from __future__ import annotations

import json
import sys
import uuid
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5010"
RESULTS_PATH = Path(__file__).resolve().parent / "uat_ca04_multi_source_results.txt"

MESSAGE = "On puc allotjar i què fer aquest cap de setmana a Girona?"
CATALOG_TOOLS = frozenset({
    "search_establishments",
    "search_destinations",
    "search_events",
    "search_articles",
    "search_experiences",
    "search_routes",
})


def main() -> int:
    session_id = str(uuid.uuid4())
    url = f"{BASE.rstrip('/')}/api/chat"
    body = json.dumps({"message": MESSAGE, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    tools: list[str] = []
    text = ""
    done = False
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
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    t = ev.get("type")
                    if t == "tool_call":
                        tools.append(ev.get("tool", ""))
                    elif t == "text_chunk":
                        text += ev.get("content", ev.get("text", ""))
                    elif t == "done":
                        done = True
                        text = text or ev.get("full_text", "")

    catalog_used = sorted({t for t in tools if t in CATALOG_TOOLS})
    passed = done and len(catalog_used) >= 2
    status = "PASS" if passed else "FAIL"
    summary = (
        f"CA-04 smoke — {status}\n"
        f"message: {MESSAGE}\n"
        f"tools: {tools}\n"
        f"catalog_tools: {catalog_used}\n"
        f"done: {done}\n"
    )
    print(summary)
    if text:
        preview = (text[:200] + "…") if len(text) > 200 else text
        print(f"reply preview: {preview!r}")
    RESULTS_PATH.write_text(summary, encoding="utf-8")
    print(f"Results written to {RESULTS_PATH}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
