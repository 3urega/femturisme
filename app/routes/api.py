import json
import uuid
from flask import Blueprint, request, Response, stream_with_context, session, jsonify, current_app
from ..services.agent_service import AgentService

api_bp = Blueprint('api', __name__)


def _get_agent():
    return AgentService(
        provider=current_app.config['LLM_PROVIDER'],
        max_iterations=current_app.config['MAX_TOOL_ITERATIONS'],
    )


@api_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    session_id   = data.get('session_id') or str(uuid.uuid4())

    if not user_message:
        return jsonify({'error': 'message required'}), 400

    agent = _get_agent()

    def generate():
        for event in agent.run(user_message, session_id):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )


@api_bp.route('/session/reset', methods=['POST'])
def reset_session():
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    if session_id:
        AgentService.clear_history(session_id)
    return jsonify({'ok': True})
