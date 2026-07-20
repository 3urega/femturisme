"""Minimal admin API authentication (tecnic §10.3, §12.1)."""
from __future__ import annotations

from functools import wraps

from flask import current_app, jsonify, request

ADMIN_TOKEN_COOKIE = 'admin_api_token'


def expected_admin_token() -> str:
    return str(current_app.config.get('ADMIN_API_TOKEN', '') or '').strip()


def admin_token_from_request() -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
        if token:
            return token

    cookie_token = request.cookies.get(ADMIN_TOKEN_COOKIE, '').strip()
    return cookie_token or None


def is_admin_authenticated() -> bool:
    expected = expected_admin_token()
    if not expected:
        return True
    provided = admin_token_from_request()
    return provided == expected


def require_admin_token(view):
    """Require Bearer token or admin cookie when ADMIN_API_TOKEN is configured."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_authenticated():
            return jsonify({'error': 'unauthorized'}), 401
        return view(*args, **kwargs)

    return wrapped


def require_admin_html(view):
    """Protect HTML admin routes with the same token contract as the API."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_authenticated():
            return jsonify({'error': 'unauthorized'}), 401
        return view(*args, **kwargs)

    return wrapped
