"""Database connections and health pings for MySQL and PostgreSQL."""
from __future__ import annotations

from typing import Any, Mapping

from app.config import Config


class DatabaseError(Exception):
    """Raised when a database operation fails."""


_CONFIG_KEYS = (
    'MYSQL_HOST',
    'MYSQL_PORT',
    'MYSQL_USER',
    'MYSQL_PASSWORD',
    'MYSQL_DATABASE',
    'MYSQL_CONNECT_TIMEOUT',
    'POSTGRES_HOST',
    'POSTGRES_PORT',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_DATABASE',
    'POSTGRES_CONNECT_TIMEOUT',
)


def _resolve_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    if config is not None:
        return dict(config)

    try:
        from flask import current_app

        return dict(current_app.config)
    except RuntimeError:
        return {key: getattr(Config, key) for key in _CONFIG_KEYS}


def _is_mysql_configured(cfg: Mapping[str, Any]) -> bool:
    return bool(str(cfg.get('MYSQL_HOST', '')).strip())


def _is_postgres_configured(cfg: Mapping[str, Any]) -> bool:
    return bool(str(cfg.get('POSTGRES_HOST', '')).strip())


def get_mysql_connection(config: Mapping[str, Any] | None = None):
    """Open a PyMySQL connection using app config or an explicit mapping."""
    import pymysql
    from pymysql.cursors import DictCursor

    cfg = _resolve_config(config)
    if not _is_mysql_configured(cfg):
        raise DatabaseError('MySQL is not configured (MYSQL_HOST is empty)')

    try:
        return pymysql.connect(
            host=cfg['MYSQL_HOST'],
            port=int(cfg.get('MYSQL_PORT', 3306)),
            user=cfg.get('MYSQL_USER', ''),
            password=cfg.get('MYSQL_PASSWORD', ''),
            database=cfg.get('MYSQL_DATABASE', 'femturisme'),
            connect_timeout=int(cfg.get('MYSQL_CONNECT_TIMEOUT', 5)),
            cursorclass=DictCursor,
        )
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


def get_postgres_connection(config: Mapping[str, Any] | None = None):
    """Open a psycopg2 connection using app config or an explicit mapping."""
    import psycopg2

    cfg = _resolve_config(config)
    if not _is_postgres_configured(cfg):
        raise DatabaseError('PostgreSQL is not configured (POSTGRES_HOST is empty)')

    try:
        return psycopg2.connect(
            host=cfg['POSTGRES_HOST'],
            port=int(cfg.get('POSTGRES_PORT', 5432)),
            user=cfg.get('POSTGRES_USER', ''),
            password=cfg.get('POSTGRES_PASSWORD', ''),
            dbname=cfg.get('POSTGRES_DATABASE', 'agent_femturisme'),
            connect_timeout=int(cfg.get('POSTGRES_CONNECT_TIMEOUT', 5)),
        )
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


def ping_mysql(config: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Check MySQL connectivity. Never raises; returns a status dict."""
    cfg = _resolve_config(config)
    if not _is_mysql_configured(cfg):
        return {'status': 'not_configured'}

    conn = None
    try:
        conn = get_mysql_connection(cfg)
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'error', 'error': str(exc)}
    finally:
        if conn is not None:
            conn.close()


def ping_postgres(config: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Check PostgreSQL connectivity. Never raises; returns a status dict."""
    cfg = _resolve_config(config)
    if not _is_postgres_configured(cfg):
        return {'status': 'not_configured'}

    conn = None
    try:
        conn = get_postgres_connection(cfg)
        with conn.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return {'status': 'ok'}
    except Exception as exc:
        return {'status': 'error', 'error': str(exc)}
    finally:
        if conn is not None:
            conn.close()


def build_health_payload() -> dict[str, object]:
    """Aggregate service and database ping status for GET /health."""
    from flask import current_app

    return {
        'ok': True,
        'service': 'up',
        'started_at': current_app.config.get('STARTED_AT'),
        'agent_features': {
            'period_hints': True,
            'territory_wide': True,
            'destination_url_prefix': 'pobles',
        },
        'mysql': ping_mysql(),
        'postgres': ping_postgres(),
    }
