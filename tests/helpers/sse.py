"""SSE stream parsing for API tests."""
from __future__ import annotations

import json


def parse_sse_events(raw: bytes | str) -> list[dict]:
    """Parse SSE body into a list of JSON event dicts."""
    if isinstance(raw, bytes):
        text = raw.decode('utf-8')
    else:
        text = raw

    events: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('data:'):
            continue
        payload = line[len('data:'):].strip()
        if payload:
            events.append(json.loads(payload))
    return events
