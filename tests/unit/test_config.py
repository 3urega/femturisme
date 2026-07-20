"""Unit tests for app.config — issue #1."""
from __future__ import annotations

import importlib
import sys


def _config_module():
    """Return app.config module (not Flask's config dict shadowed on app package)."""
    mod = sys.modules.get('app.config')
    if mod is None or not hasattr(mod, '_env'):
        mod = importlib.import_module('app.config')
    return mod


def test_testing_config_exposes_mysql_and_postgres(app):
    """Flask testing config includes DB settings with safe defaults."""
    cfg = app.config
    assert 'MYSQL_HOST' in cfg
    assert 'MYSQL_PORT' in cfg
    assert isinstance(cfg['MYSQL_PORT'], int)
    assert cfg['MYSQL_PORT'] > 0
    assert cfg['MYSQL_DATABASE']
    assert 'POSTGRES_HOST' in cfg
    assert isinstance(cfg['POSTGRES_PORT'], int)
    assert cfg['POSTGRES_PORT'] > 0
    assert cfg['POSTGRES_DATABASE']
    assert cfg.get('POSTGRES_SSLMODE') is not None or cfg.get('POSTGRES_HOST', '')
    assert cfg['LOG_LEVEL'] == 'INFO'
    assert cfg['EMBEDDING_MODEL'] == 'text-embedding-3-small'
    assert cfg['DOCUMENT_STORAGE_PATH'] == 'data/guides'
    assert cfg.get('STORAGE_BACKEND', 'local') == 'local'
    assert 'S3_ENDPOINT' in cfg
    assert cfg.get('S3_BUCKET') == 'guides'


def test_env_prefers_agent_prefix(monkeypatch):
    """AGENT_MYSQL_HOST takes precedence over MYSQL_HOST."""
    monkeypatch.setenv('AGENT_MYSQL_HOST', 'from-agent')
    monkeypatch.setenv('MYSQL_HOST', 'from-plain')

    config_module = importlib.reload(_config_module())

    assert config_module._env('MYSQL_HOST') == 'from-agent'

    monkeypatch.delenv('AGENT_MYSQL_HOST', raising=False)
    importlib.reload(_config_module())


def test_env_int_invalid_falls_back_to_default(monkeypatch):
    """Invalid MYSQL_PORT uses default 3306."""
    monkeypatch.setenv('MYSQL_PORT', 'not-a-number')

    config_module = importlib.reload(_config_module())

    assert config_module._env_int('MYSQL_PORT', 3306) == 3306

    monkeypatch.delenv('MYSQL_PORT', raising=False)
    importlib.reload(_config_module())
