"""Admin API routes for RAG entities and documents (tecnic §9.4–9.6)."""
from __future__ import annotations

import uuid

from flask import Blueprint, current_app, jsonify, request

from app.db.connection import DatabaseError
from app.db.repositories import documents as documents_repo
from app.db.repositories import entities as entities_repo
from app.services.admin_auth import require_admin_token
from app.services.document_storage import (
    DocumentStorageError,
    InvalidPdfError,
    build_storage_path,
    purge_document_storage,
    save_original,
    validate_pdf,
)
from app.services.embedding_service import EmbeddingError
from app.services.indexing_pipeline import schedule_indexing

admin_bp = Blueprint('admin', __name__)


def _json_error(message: str, status: int):
    return jsonify({'error': message}), status


def _pipeline_config() -> dict:
    return dict(current_app.config)


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
    config = _pipeline_config()
    try:
        documents = documents_repo.list_all(entity_id=entity_id, config=config)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)

    try:
        for document in documents:
            purge_document_storage(document['doc_id'], config=config)
    except DocumentStorageError as exc:
        return _json_error(str(exc), 500)

    try:
        deleted = entities_repo.delete(entity_id, config=config)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if not deleted:
        return _json_error('entity not found', 404)
    return jsonify({'ok': True})


@admin_bp.route('/documents/upload', methods=['POST'])
@require_admin_token
def upload_document():
    entity_id = request.form.get('entity_id', '').strip()
    title = request.form.get('title', '').strip()
    category = request.form.get('category')
    upload = request.files.get('file')

    if not entity_id:
        return _json_error('entity_id is required', 400)
    if not title:
        return _json_error('title is required', 400)
    if upload is None or not upload.filename:
        return _json_error('file is required', 400)

    try:
        entity = entities_repo.get_by_id(entity_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if entity is None:
        return _json_error('entity not found', 404)
    if entity.get('is_active') is False:
        return _json_error('entity is not active', 400)

    file_data = upload.read()
    try:
        validate_pdf(file_data, upload.content_type)
    except InvalidPdfError as exc:
        return _json_error(str(exc), 400)

    doc_id = uuid.uuid4()
    storage_path = build_storage_path(doc_id)
    document = None
    try:
        document = documents_repo.create(
            doc_id=doc_id,
            entity_id=entity_id,
            title=title,
            category=category,
            source_filename=upload.filename,
            storage_path=storage_path,
        )
        save_original(doc_id, file_data)
    except documents_repo.DocumentValidationError as exc:
        return _json_error(str(exc), 400)
    except (DatabaseError, DocumentStorageError) as exc:
        if document is not None:
            try:
                documents_repo.delete(doc_id)
            except DatabaseError:
                pass
            try:
                purge_document_storage(doc_id)
            except DocumentStorageError:
                pass
        return _json_error(str(exc), 500)

    schedule_indexing(doc_id, config=_pipeline_config())

    return jsonify(document), 201


@admin_bp.route('/documents', methods=['GET'])
@require_admin_token
def list_documents():
    entity_id = request.args.get('entity_id')
    if entity_id is not None:
        entity_id = entity_id.strip()
        if not entity_id:
            return _json_error('entity_id must not be empty', 400)
        try:
            uuid.UUID(entity_id)
        except ValueError:
            return _json_error('entity_id must be a valid UUID', 400)

    try:
        rows = documents_repo.list_all(entity_id=entity_id or None)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    return jsonify({'documents': rows, 'total': len(rows)})


@admin_bp.route('/documents/<uuid:doc_id>', methods=['GET'])
@require_admin_token
def get_document(doc_id):
    try:
        document = documents_repo.get_by_id(doc_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if document is None:
        return _json_error('document not found', 404)
    return jsonify(document)


@admin_bp.route('/documents/<uuid:doc_id>', methods=['DELETE'])
@require_admin_token
def delete_document(doc_id):
    try:
        deleted = documents_repo.delete(doc_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if not deleted:
        return _json_error('document not found', 404)

    try:
        purge_document_storage(doc_id)
    except DocumentStorageError as exc:
        return _json_error(str(exc), 500)

    return jsonify({'ok': True})


@admin_bp.route('/documents/<uuid:doc_id>/reindex', methods=['POST'])
@require_admin_token
def reindex_document(doc_id):
    try:
        document = documents_repo.get_by_id(doc_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if document is None:
        return _json_error('document not found', 404)

    schedule_indexing(doc_id, reindex=True, config=_pipeline_config())
    return jsonify({'ok': True, 'doc_id': str(doc_id), 'status': 'extracting'}), 202


@admin_bp.route('/documents/<uuid:doc_id>/smoke-test', methods=['POST'])
@require_admin_token
def smoke_test_document(doc_id):
    data = request.get_json(silent=True) or {}
    query = str(data.get('query') or '').strip()
    if not query:
        return _json_error('query is required', 400)

    try:
        document = documents_repo.get_by_id(doc_id)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)
    if document is None:
        return _json_error('document not found', 404)
    if document.get('status') != 'indexed':
        return _json_error('document is not indexed', 400)

    limit = data.get('limit', 5)
    try:
        resolved_limit = int(limit) if limit is not None else 5
    except (TypeError, ValueError):
        resolved_limit = 5
    resolved_limit = max(1, min(resolved_limit, 20))

    try:
        result = documents_repo.search(
            query=query,
            entity_id=document['entity_id'],
            doc_id=doc_id,
            limit=resolved_limit,
            config=_pipeline_config(),
        )
    except documents_repo.SearchValidationError as exc:
        return _json_error(str(exc), 400)
    except documents_repo.EntityNotFoundError as exc:
        return _json_error(str(exc), 404)
    except EmbeddingError as exc:
        return _json_error(str(exc), 500)
    except DatabaseError as exc:
        return _json_error(str(exc), 500)

    return jsonify(result)
