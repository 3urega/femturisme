import os

from dotenv import load_dotenv

load_dotenv()


def _env(key, default=None):
    return os.environ.get(f'AGENT_{key}', os.environ.get(key, default))


def _env_int(key, default):
    raw = _env(key)
    if raw is None or raw == '':
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _env_bool(key, default=True):
    raw = _env(key)
    if raw is None or raw == '':
        return default
    return str(raw).strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    SECRET_KEY = _env('SECRET_KEY', 'dev-secret-change-me')

    # LLM provider: dummy | anthropic | openai | gemini
    LLM_PROVIDER = _env('LLM_PROVIDER', 'dummy')

    ANTHROPIC_API_KEY = _env('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL   = _env('ANTHROPIC_MODEL', 'claude-haiku-4-5-20251001')

    OPENAI_API_KEY = _env('OPENAI_API_KEY')
    OPENAI_MODEL   = _env('OPENAI_MODEL', 'gpt-4.1-mini')

    GEMINI_API_KEY = _env('GEMINI_API_KEY')
    GEMINI_MODEL   = _env('GEMINI_MODEL', 'gemini-3.1-flash-lite')

    MAX_TOOL_ITERATIONS = _env_int('MAX_TOOL_ITERATIONS', 5)

    # MySQL femturisme CMS (read-only)
    MYSQL_HOST = _env('MYSQL_HOST', '')
    MYSQL_PORT = _env_int('MYSQL_PORT', 3306)
    MYSQL_USER = _env('MYSQL_USER', '')
    MYSQL_PASSWORD = _env('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = _env('MYSQL_DATABASE', 'femturisme')
    MYSQL_CONNECT_TIMEOUT = _env_int('MYSQL_CONNECT_TIMEOUT', 5)

    # PostgreSQL agent (RAG / documents)
    POSTGRES_HOST = _env('POSTGRES_HOST', '')
    POSTGRES_PORT = _env_int('POSTGRES_PORT', 5432)
    POSTGRES_USER = _env('POSTGRES_USER', '')
    POSTGRES_PASSWORD = _env('POSTGRES_PASSWORD', '')
    POSTGRES_DATABASE = _env('POSTGRES_DATABASE', 'agent_femturisme')
    POSTGRES_CONNECT_TIMEOUT = _env_int('POSTGRES_CONNECT_TIMEOUT', 5)
    # disable | allow | prefer | require | verify-ca | verify-full
    POSTGRES_SSLMODE = _env('POSTGRES_SSLMODE', '')

    # Ops / embeddings
    LOG_LEVEL = _env('LOG_LEVEL', 'INFO')
    REQUEST_LOGGING_ENABLED = _env_bool('REQUEST_LOGGING_ENABLED', True)
    RATE_LIMIT_PER_IP = _env_int('RATE_LIMIT_PER_IP', 30)
    RATE_LIMIT_PER_SESSION = _env_int('RATE_LIMIT_PER_SESSION', 20)
    RATE_LIMIT_WINDOW_SECONDS = _env_int('RATE_LIMIT_WINDOW_SECONDS', 60)
    EMBEDDING_MODEL = _env('EMBEDDING_MODEL', 'text-embedding-3-small')
    DOCUMENT_STORAGE_PATH = _env('DOCUMENT_STORAGE_PATH', 'data/guides')

    # Document storage: local filesystem (default) or Supabase S3-compatible
    STORAGE_BACKEND = _env('STORAGE_BACKEND', 'local').strip().lower()
    S3_ENDPOINT = _env('S3_ENDPOINT', '')
    S3_REGION = _env('S3_REGION', 'eu-central-1')
    S3_BUCKET = _env('S3_BUCKET', 'guides')
    S3_ACCESS_KEY_ID = _env('S3_ACCESS_KEY_ID', '')
    S3_SECRET_ACCESS_KEY = _env('S3_SECRET_ACCESS_KEY', '')

    # Admin API (RAG entities/documents) — empty token = open in dev (tecnic §12.1)
    ADMIN_API_TOKEN = _env('ADMIN_API_TOKEN', '')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    LLM_PROVIDER = 'dummy'
    MAX_TOOL_ITERATIONS = 3
    RATE_LIMIT_PER_IP = 9999
    RATE_LIMIT_PER_SESSION = 9999
    STORAGE_BACKEND = 'local'
    S3_ENDPOINT = ''
    S3_ACCESS_KEY_ID = ''
    S3_SECRET_ACCESS_KEY = ''


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
