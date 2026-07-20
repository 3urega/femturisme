"""Minimal admin API authentication (tecnic §10.3, §12.1)."""
from __future__ import annotations

from functools import wraps

from flask import current_app, jsonify, request


def _extract_bearer_token() -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:].strip()
    return token or None


def require_admin_token(view):
    """Require Bearer token when ADMIN_API_TOKEN is configured."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = str(current_app.config.get('ADMIN_API_TOKEN', '') or '').strip()
        if not expected:
            return view(*args, **kwargs)

        provided = _extract_bearer_token()
        if provided != expected:
            return jsonify({'error': 'unauthorized'}), 401
        return view(*args, **kwargs)

    return wrapped
