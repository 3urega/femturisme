"""
End-to-end agent loop test — uses DUMMY provider + real scraper tools.
Verifies the full flow without needing API keys.
"""
import sys, os
sys.path.insert(0, '/projects/agent')
sys.path.insert(0, '/projects/restaurants/venv/lib/python3.11/site-packages')
os.environ.setdefault('AGENT_SECRET_KEY', 'test')
os.environ.setdefault('AGENT_LLM_PROVIDER', 'dummy')

from app import create_app

app = create_app()

with app.app_context():
    from app.services.agent_service import AgentService

    svc = AgentService(provider='dummy', max_iterations=5)
    session = 'test-session-001'

    queries = [
        'Quines rutes de senderisme hi ha al Berguedà?',
        'Events a Tarragona aquest mes',
        'On puc dormir a la Costa Brava?',
        'Experiències gastronòmiques a Girona',
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print('='*60)
        for event in svc.run(q, session):
            t = event.get('type')
            if t == 'tool_call':
                print(f"  [tool_call]   {event['tool']}({event['input']})")
            elif t == 'tool_result':
                res = event['result']
                total = res.get('total', '?')
                results = res.get('results', [])
                print(f"  [tool_result] total={total}, got {len(results)} cards")
                for r in results[:2]:
                    print(f"    • {r.get('title','?')} — {r.get('location','?')}")
            elif t == 'text_chunk':
                print(f"  [text]  {event['content'][:80]}", end='')
            elif t == 'done':
                print(f"\n  [done]")
            elif t == 'error':
                print(f"  [error] {event['message']}")
        # Reset between queries so each is independent
        AgentService.clear_history(session)
