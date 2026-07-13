import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    # Reloader kills in-flight SSE when files change; disable for manual chat testing.
    use_reloader = os.environ.get('AGENT_USE_RELOADER', '').lower() in ('1', 'true', 'yes')
    app.run(debug=True, port=port, threaded=True, use_reloader=use_reloader)
