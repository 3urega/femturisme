"""Smoke tests for admin HTML routes (issue #32)."""
from __future__ import annotations


def test_admin_guides_list_returns_200(client):
    response = client.get('/admin/guides')
    assert response.status_code == 200
    assert b'Guies PDF' in response.data


def test_admin_guides_upload_returns_200(client):
    response = client.get('/admin/guides/upload')
    assert response.status_code == 200
    assert b'Pujar guia PDF' in response.data


def test_admin_guides_detail_returns_200(client):
    doc_id = '550e8400-e29b-41d4-a716-446655440000'
    response = client.get(f'/admin/guides/{doc_id}')
    assert response.status_code == 200
    assert doc_id.encode() in response.data
