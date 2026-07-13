"""Simulate: Quins events i fires hi ha a Catalunya aquest mes?"""
from __future__ import annotations

import json

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.services.tools import execute_tool

QUESTION = "Quins events i fires hi ha a Catalunya aquest mes?"

app = create_app()
with app.app_context():
    tool_input = {
        "destination": "Catalunya",
        "date_from": "2026-07-01",
        "date_to": "2026-07-31",
    }
    raw = execute_tool("search_events", tool_input)
    data = json.loads(raw)

    print("PREGUNTA USUARI:")
    print(f"  {QUESTION}")
    print()
    print("TOOL CALL (el que hauria de fer el LLM):")
    print(f"  search_events({json.dumps(tool_input, ensure_ascii=False)})")
    print()
    print("TOOL RESULT:")
    print(f"  total: {data.get('total')}")
    print(f"  error: {data.get('error')}")
    print(f"  meta: {json.dumps(data.get('meta'), ensure_ascii=False)}")
    print()
    print("RESULTATS (fins a 10):")
    for i, row in enumerate(data.get("results", [])[:10], 1):
        print(f"  {i}. {row.get('title')}")
        print(f"     Ubicació: {row.get('location')}")
        print(f"     Data: {row.get('date')}")
        print(f"     URL: {row.get('url')}")
    print()
    total = int(data.get("total", 0) or 0)
    if total > 10:
        print(f"  (... i {total - 10} més al catàleg, limitats a 20 per consulta)")
