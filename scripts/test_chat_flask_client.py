"""Flask test_client chat probe."""
from __future__ import annotations

import json
import sys

import _bootstrap  # noqa: F401 — add project root to sys.path

from dotenv import load_dotenv

load_dotenv()

from app import create_app

MESSAGE = sys.argv[1] if len(sys.argv) > 1 else "Què fer aquest cap de setmana a l'Empordà"


def main() -> None:
    app = create_app()
    client = app.test_client()
    resp = client.post(
        "/api/chat",
        json={"message": MESSAGE, "session_id": "test-emporda-probe"},
    )
    print("status", resp.status_code)
    data = resp.get_data(as_text=True)
    events: list[dict] = []
    for block in data.split("\n\n"):
        for line in block.split("\n"):
            if not line.startswith("data: "):
                continue
            raw = line[6:].strip()
            if not raw or raw == "[DONE]":
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                pass

    for e in events:
        t = e.get("type")
        if t == "tool_call":
            print("TOOL_CALL", e.get("tool"), json.dumps(e.get("input"), ensure_ascii=False))
        elif t == "tool_result":
            r = e.get("result", {})
            total = r.get("total") if isinstance(r, dict) else None
            err = r.get("error") if isinstance(r, dict) else None
            print("TOOL_RESULT", e.get("tool"), "total=", total, "error=", err)
        elif t == "text_chunk":
            print("CHUNK", repr((e.get("content") or "")[:120]))
        elif t == "error":
            print("ERROR", e.get("message"))
        elif t == "done":
            print("DONE")

    text = "".join(e.get("content", "") for e in events if e.get("type") == "text_chunk")
    print("---RESPUESTA---")
    print(text if text else "(sin texto)")
    print("---EVENT TYPES---")
    print([e.get("type") for e in events])


if __name__ == "__main__":
    main()
