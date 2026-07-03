import os


def _env(key, default=None):
    return os.environ.get(f'AGENT_{key}', os.environ.get(key, default))


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

    MAX_TOOL_ITERATIONS = int(_env('MAX_TOOL_ITERATIONS', 5))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    LLM_PROVIDER = 'dummy'
    MAX_TOOL_ITERATIONS = 3


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
    'default':     DevelopmentConfig,
}
