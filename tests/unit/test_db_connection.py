"""Unit tests for app.db.connection — issue #3."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.db.connection import (
    DatabaseError,
    get_mysql_connection,
    ping_mysql,
    ping_postgres,
)
from app.db.mappers import row_to_card


def test_ping_mysql_not_configured():
    result = ping_mysql({'MYSQL_HOST': ''})
    assert result == {'status': 'not_configured'}


def test_ping_postgres_not_configured():
    result = ping_postgres({'POSTGRES_HOST': ''})
    assert result == {'status': 'not_configured'}


def test_ping_mysql_error_when_unreachable():
    cfg = {
        'MYSQL_HOST': '127.0.0.1',
        'MYSQL_PORT': 3306,
        'MYSQL_USER': 'agent_read',
        'MYSQL_PASSWORD': 'wrong',
        'MYSQL_DATABASE': 'femturisme',
        'MYSQL_CONNECT_TIMEOUT': 1,
    }
    result = ping_mysql(cfg)
    assert result['status'] == 'error'
    assert 'error' in result


def test_ping_postgres_error_when_unreachable():
    cfg = {
        'POSTGRES_HOST': '127.0.0.1',
        'POSTGRES_PORT': 5432,
        'POSTGRES_USER': 'agent_app',
        'POSTGRES_PASSWORD': 'wrong',
        'POSTGRES_DATABASE': 'agent_femturisme',
        'POSTGRES_CONNECT_TIMEOUT': 1,
    }
    result = ping_postgres(cfg)
    assert result['status'] == 'error'
    assert 'error' in result


@patch('pymysql.connect')
def test_ping_mysql_ok(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    cfg = {
        'MYSQL_HOST': 'localhost',
        'MYSQL_PORT': 3306,
        'MYSQL_USER': 'agent_read',
        'MYSQL_PASSWORD': 'secret',
        'MYSQL_DATABASE': 'femturisme',
        'MYSQL_CONNECT_TIMEOUT': 5,
    }
    result = ping_mysql(cfg)

    assert result == {'status': 'ok'}
    mock_cursor.execute.assert_called_once_with('SELECT 1')
    mock_conn.close.assert_called_once()


def test_get_mysql_connection_raises_when_not_configured():
    try:
        get_mysql_connection({'MYSQL_HOST': ''})
        assert False, 'expected DatabaseError'
    except DatabaseError as exc:
        assert 'not configured' in str(exc).lower()


def test_row_to_card_not_implemented():
    try:
        row_to_card({'id': 1, 'title': 'Test'}, 'establishment')
        assert False, 'expected NotImplementedError'
    except NotImplementedError as exc:
        assert 'establishment' in str(exc)
