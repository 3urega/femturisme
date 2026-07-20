"""Tool: search_entity_knowledge — semantic search in entity document knowledge base."""
from __future__ import annotations

import json

from app.db.connection import DatabaseError
from app.db.repositories import documents as documents_repo
from app.services.embedding_service import EmbeddingError

SCHEMA = {
    'name': 'search_entity_knowledge',
    'description': (
        'Search indexed PDF guides and entity knowledge base by semantic similarity. '
        'Use for practical information from entity documents: opening hours, parking, '
        'history, services, and similar content tied to a specific entity_id.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': 'Semantic search query within indexed entity documents.',
            },
            'entity_id': {
                'type': 'string',
                'description': 'UUID of the entity (entities.entity_id).',
            },
            'category': {
                'type': 'string',
                'description': 'Optional document category filter, e.g. patrimoni, festes.',
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of chunks to return (default 5).',
            },
        },
        'required': ['query', 'entity_id'],
    },
}


def _error_payload(message: str, *, query: str, entity_id: str) -> dict:
    return {
        'query': query,
        'entity_id': entity_id,
        'total': 0,
        'results': [],
        'error': message,
    }


def execute(tool_input: dict) -> str:
    query = str(tool_input.get('query') or '')
    entity_id = str(tool_input.get('entity_id') or '')
    category = tool_input.get('category')
    limit = tool_input.get('limit', 5)

    try:
        resolved_limit = int(limit) if limit is not None else 5
    except (TypeError, ValueError):
        resolved_limit = 5
    resolved_limit = max(1, min(resolved_limit, 20))

    try:
        result = documents_repo.search(
            query=query,
            entity_id=entity_id,
            limit=resolved_limit,
            category=category,
        )
    except documents_repo.SearchValidationError as exc:
        return json.dumps(_error_payload(str(exc), query=query, entity_id=entity_id))
    except documents_repo.EntityNotFoundError as exc:
        return json.dumps(_error_payload(str(exc), query=query, entity_id=entity_id))
    except EmbeddingError as exc:
        return json.dumps(_error_payload(str(exc), query=query, entity_id=entity_id))
    except DatabaseError as exc:
        return json.dumps(_error_payload(str(exc), query=query, entity_id=entity_id))

    return json.dumps(result)
