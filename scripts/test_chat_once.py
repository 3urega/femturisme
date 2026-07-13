"""One-shot chat test against running Flask server."""
from __future__ import annotations

import json
import sys
import uuid
import urllib.request

MESSAGE = sys.argv[1] if len(sys.argv) > 1 else "Què fer aquest cap de setmana a l'Empordà"
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5010"


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
    with urllib.request.urlopen(req, timeout=120) as resp:
        print(f"STATUS {resp.status}")
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
                        print("TOOL_CALL", tool, json.dumps(ev.get("input", {}), ensure_ascii=False))
                    elif t == "tool_result":
                        res = ev.get("result", {})
                        total = res.get("total") if isinstance(res, dict) else None
                        print("TOOL_RESULT", ev.get("tool"), "total=", total)
                    elif t == "text_chunk":
                        text += ev.get("content", ev.get("text", ""))
                    elif t == "error":
                        print("ERROR", ev.get("message"))
                    elif t == "done":
                        print("DONE")
                    else:
                        print("EVENT", json.dumps(ev, ensure_ascii=False)[:800])

    print("---RESPUESTA---")
    print(text.strip() if text.strip() else "(sin texto)")
    print("---TOOLS---")
    print(", ".join(tools) if tools else "(ninguna)")


if __name__ == "__main__":
    main()
