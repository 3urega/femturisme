import json
import uuid
from flask import Blueprint, request, Response, stream_with_context, jsonify, current_app
from ..services.agent_service import AgentService
from ..services.chat_context import (
    ChatContextError,
    EntityModeNotAvailableError,
    parse_chat_request,
    validate_agent_context,
)

api_bp = Blueprint('api', __name__)


def _get_agent():
    return AgentService(
        provider=current_app.config['LLM_PROVIDER'],
        max_iterations=current_app.config['MAX_TOOL_ITERATIONS'],
    )


@api_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    try:
        user_message, session_id, page_context, agent_context = parse_chat_request(data)
        validate_agent_context(agent_context)
    except ChatContextError as exc:
        return jsonify({'error': str(exc)}), 400
    except EntityModeNotAvailableError as exc:
        return jsonify({'error': str(exc)}), 501

    if not user_message:
        return jsonify({'error': 'message required'}), 400

    if not session_id:
        session_id = str(uuid.uuid4())

    agent = _get_agent()

    def generate():
        try:
            for event in agent.run(
                user_message,
                session_id,
                page_context=page_context,
                agent_context=agent_context,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as exc:
            err = {'type': 'error', 'message': str(exc)}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

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
