"""SSE chat probe with proper streaming read (no early EOF)."""
from __future__ import annotations

import json
import sys
import uuid

import urllib.request

MESSAGE = sys.argv[1] if len(sys.argv) > 1 else "Què fer aquest cap de setmana a l'Empordà"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5010"
TIMEOUT = int(sys.argv[3]) if len(sys.argv) > 3 else 120


def main() -> None:
    url = f"{BASE.rstrip('/')}/api/chat"
    body = json.dumps({"message": MESSAGE, "session_id": str(uuid.uuid4())}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    tools: list[str] = []
    text = ""
    types: list[str] = []

    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        print(f"STATUS {resp.status}")
        buffer = ""
        while True:
            chunk = resp.read(1)
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
                    types.append(t or "?")
                    if t == "tool_call":
                        tools.append(ev.get("tool", ""))
                        print("TOOL_CALL", ev.get("tool"), json.dumps(ev.get("input"), ensure_ascii=False))
                    elif t == "tool_result":
                        res = ev.get("result", {})
                        total = res.get("total") if isinstance(res, dict) else None
                        print("TOOL_RESULT", ev.get("tool"), "total=", total)
                    elif t == "text_chunk":
                        text += ev.get("content", "")
                    elif t == "error":
                        print("ERROR", ev.get("message"))
                    elif t == "done":
                        print("DONE")

    print("---RESPUESTA---")
    print(text.strip() if text.strip() else "(sin texto)")
    print("---TYPES---", types)


if __name__ == "__main__":
    main()
