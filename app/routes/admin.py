"""Admin API routes for RAG entities (tecnic §9.4)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.db.connection import DatabaseError
from app.db.repositories import entities as entities_repo
from app.services.admin_auth import require_admin_token

admin_bp = Blueprint('admin', __name__)


def _json_error(message: str, status: int):
    return jsonify({'error': message}), status


@admin_bp.route('/entities', methods=['POST'])
@require_admin_token
def create_entity():
    data = request.get_json(silent=True) or {}
    try:
        entity = entities_repo.create(
            name=data.get('name', ''),
            entity_type=data.get('entity_type', ''),
            slug=data.get('slug'),
            territory=data.get('territory'),
            config=data.get('config'),
        )
    except entities_repo.EntityValidationError as exc:
        return _json_error(str(exc), 400)
    except entities_repo.DuplicateSlugError as exc:
        return _json_error(str(exc), 409)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    return jsonify(entity), 201


@admin_bp.route('/entities', methods=['GET'])
@require_admin_token
def list_entities():
    try:
        rows = entities_repo.list_active()
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    return jsonify({'entities': rows, 'total': len(rows)})


@admin_bp.route('/entities/<uuid:entity_id>', methods=['GET'])
@require_admin_token
def get_entity(entity_id):
    try:
        entity = entities_repo.get_by_id(entity_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if entity is None:
        return _json_error('entity not found', 404)
    return jsonify(entity)


@admin_bp.route('/entities/<uuid:entity_id>', methods=['PUT'])
@require_admin_token
def update_entity(entity_id):
    data = request.get_json(silent=True) or {}
    try:
        entity = entities_repo.update(entity_id, fields=data)
    except entities_repo.EntityValidationError as exc:
        return _json_error(str(exc), 400)
    except entities_repo.DuplicateSlugError as exc:
        return _json_error(str(exc), 409)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if entity is None:
        return _json_error('entity not found', 404)
    return jsonify(entity)


@admin_bp.route('/entities/<uuid:entity_id>', methods=['DELETE'])
@require_admin_token
def delete_entity(entity_id):
    try:
        deleted = entities_repo.delete(entity_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if not deleted:
        return _json_error('entity not found', 404)
    return jsonify({'ok': True})
