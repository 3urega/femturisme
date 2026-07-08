from flask import Blueprint, jsonify, render_template

from app.db.connection import build_health_payload

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/health', methods=['GET'])
def health():
    return jsonify(build_health_payload())
