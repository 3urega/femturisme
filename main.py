import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    # Reloader spawns a child process on Windows and often leaves zombies on 5010.
    use_reloader = (
        debug
        and os.environ.get('AGENT_USE_RELOADER', '').lower() in ('1', 'true', 'yes')
    )
    started_at = app.config.get('STARTED_AT', '?')
    print(f' * Agent femturisme — http://127.0.0.1:{port}')
    print(f' * started_at: {started_at}')
    print(' * Smoke: GET /health must include agent_features.period_hints')
    app.run(debug=debug, port=port, threaded=True, use_reloader=use_reloader)
