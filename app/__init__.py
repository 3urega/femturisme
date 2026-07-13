import os
from datetime import datetime, timezone

from flask import Flask
from .config import config


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    app.config['STARTED_AT'] = datetime.now(timezone.utc).isoformat()

    # Blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
