"""Simulate polluted session history with old zero-result tool call."""
import json
import uuid

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.services.agent_service import AgentService, _history

QUESTION = "Quins events i fires hi ha a Catalunya aquest mes?"
SESSION = "polluted-session-test"

# Simulate previous failed exchange (June 2024, zero results)
_history[SESSION] = [
    {'role': 'user', 'content': QUESTION},
    {
        'role': 'assistant',
        'content': [
            {
                'type': 'tool_use',
                'id': 'old-tool-1',
                'name': 'search_events',
                'input': {
                    'destination': 'Catalunya',
                    'date_from': '2024-06-01',
                    'date_to': '2024-06-30',
                },
            }
        ],
    },
    {
        'role': 'user',
        'content': [
            {
                'type': 'tool_result',
                'tool_use_id': 'old-tool-1',
                'content': json.dumps({
                    'destination': 'Catalunya',
                    'total': '0',
                    'results': [],
                    'error': None,
                    'meta': {'hint': 'zero_results_territory_wide'},
                }),
            }
        ],
    },
    {
        'role': 'assistant',
        'content': (
            'Actualment no hi ha cap esdeveniment registrat per a tot Catalunya '
            'durant aquest mes de juny 2024.'
        ),
    },
]

app = create_app()
with app.app_context():
    agent = AgentService(provider=app.config['LLM_PROVIDER'])
    print('=== SECOND ASK (same session, polluted history) ===')
    for ev in agent.run(QUESTION, SESSION):
        t = ev.get('type')
        if t == 'tool_call':
            print('TOOL_CALL', ev.get('tool'), ev.get('input'))
        elif t == 'tool_result':
            r = ev.get('result', {})
            print('TOOL_RESULT', ev.get('tool'), 'total=', r.get('total'))
        elif t == 'done':
            print('---ANSWER---')
            print((ev.get('full_text') or '')[:800])
