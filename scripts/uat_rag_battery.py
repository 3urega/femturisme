"""DEV-507 — UAT RAG admin: entitats, upload, indexació, smoke-test, reindex, delete."""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[misc, assignment]

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PDF = ROOT / 'tests' / 'fixtures' / 'sample-guide.pdf'
RESULTS_FILE = ROOT / 'uat_rag_battery_results.txt'

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5010'
POLL_TIMEOUT_SECONDS = 120
POLL_INTERVAL_SECONDS = 2


@dataclass
class CaseResult:
    case_id: str
    description: str
    ok: bool = False
    error: str | None = None
    details: dict = field(default_factory=dict)


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / '.env')


def _admin_headers() -> dict[str, str]:
    token = str(os.environ.get('ADMIN_API_TOKEN', '') or '').strip()
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def _request_json(
    method: str,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> tuple[int, dict | list | None]:
    req_headers = dict(_admin_headers())
    if headers:
        req_headers.update(headers)
    request = Request(url, data=data, headers=req_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            body = json.loads(raw) if raw else None
            return response.status, body
    except HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = {'error': raw or exc.reason}
        return exc.code, body


def _multipart_upload(
    url: str,
    *,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    filename: str,
) -> tuple[int, dict | None]:
    boundary = f'----UATRAG{uuid.uuid4().hex}'
    content_type = mimetypes.guess_type(filename)[0] or 'application/pdf'
    file_bytes = file_path.read_bytes()

    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f'{value}\r\n'
            ).encode('utf-8')
        )
    parts.append(
        (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8')
        + file_bytes
        + b'\r\n'
    )
    parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
    body = b''.join(parts)

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
    }
    return _request_json('POST', url, data=body, headers=headers, timeout=120)


def _poll_document(
    base: str,
    doc_id: str,
    *,
    expect_status: str = 'indexed',
) -> dict:
    deadline = time.time() + POLL_TIMEOUT_SECONDS
    url = f'{base.rstrip("/")}/admin/api/documents/{doc_id}'
    last: dict | None = None
    while time.time() < deadline:
        status, body = _request_json('GET', url)
        if status != 200 or not isinstance(body, dict):
            raise RuntimeError(f'poll failed HTTP {status}: {body}')
        last = body
        current = body.get('status')
        if current == expect_status:
            return body
        if current == 'failed':
            raise RuntimeError(body.get('error_message') or 'indexing failed')
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(
        f'timeout waiting for status={expect_status}, last={last.get("status") if last else None}'
    )


def run_battery(base: str) -> list[CaseResult]:
    if not SAMPLE_PDF.is_file():
        raise FileNotFoundError(f'missing fixture PDF: {SAMPLE_PDF}')

    api = f'{base.rstrip("/")}/admin/api'
    results: list[CaseResult] = []
    entity_id: str | None = None
    doc_id: str | None = None
    version_before_reindex: int | None = None

    # UAT-RAG-01 — create entity
    case01 = CaseResult('UAT-RAG-01', 'POST /admin/api/entities')
    suffix = uuid.uuid4().hex[:8]
    status, body = _request_json(
        'POST',
        f'{api}/entities',
        data=json.dumps({
            'name': f'UAT RAG entity {suffix}',
            'entity_type': 'museu',
            'slug': f'uat-rag-{suffix}',
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    if status == 201 and isinstance(body, dict) and body.get('entity_id'):
        entity_id = str(body['entity_id'])
        case01.ok = True
        case01.details = {'entity_id': entity_id}
    else:
        case01.error = f'HTTP {status}: {body}'
    results.append(case01)
    if not case01.ok:
        return results

    # UAT-RAG-02 — upload + poll indexed
    case02 = CaseResult('UAT-RAG-02', 'Upload PDF and wait for indexed')
    status, body = _multipart_upload(
        f'{api}/documents/upload',
        fields={
            'entity_id': entity_id,
            'title': f'UAT guide {suffix}',
            'category': 'patrimoni',
        },
        file_field='file',
        file_path=SAMPLE_PDF,
        filename='sample-guide.pdf',
    )
    if status == 201 and isinstance(body, dict) and body.get('doc_id'):
        doc_id = str(body['doc_id'])
        try:
            indexed = _poll_document(base, doc_id)
            case02.ok = (
                indexed.get('status') == 'indexed'
                and int(indexed.get('chunks_count') or 0) > 0
            )
            case02.details = {
                'doc_id': doc_id,
                'chunks_count': indexed.get('chunks_count'),
            }
        except Exception as exc:  # noqa: BLE001
            case02.error = str(exc)
            case02.details = {'doc_id': doc_id}
    else:
        case02.error = f'HTTP {status}: {body}'
    results.append(case02)
    if not case02.ok or not doc_id:
        return results

    # UAT-RAG-03 — smoke-test
    case03 = CaseResult('UAT-RAG-03', 'POST smoke-test returns chunks')
    status, body = _request_json(
        'POST',
        f'{api}/documents/{doc_id}/smoke-test',
        data=json.dumps({'query': 'on aparcar'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
    )
    if status == 200 and isinstance(body, dict):
        total = int(body.get('total') or 0)
        first = (body.get('results') or [{}])[0] if body.get('results') else {}
        case03.ok = total >= 1 and bool(first.get('content'))
        case03.details = {'total': total}
        if not case03.ok:
            case03.error = f'unexpected body: {body}'
    else:
        case03.error = f'HTTP {status}: {body}'
    results.append(case03)

    # UAT-RAG-04 — reindex + poll
    case04 = CaseResult('UAT-RAG-04', 'Reindex increments version and re-indexes')
    status, before = _request_json('GET', f'{api}/documents/{doc_id}')
    if status == 200 and isinstance(before, dict):
        version_before_reindex = int(before.get('version') or 0)
    status, body = _request_json('POST', f'{api}/documents/{doc_id}/reindex')
    if status == 202:
        try:
            indexed = _poll_document(base, doc_id)
            new_version = int(indexed.get('version') or 0)
            case04.ok = (
                indexed.get('status') == 'indexed'
                and version_before_reindex is not None
                and new_version == version_before_reindex + 1
            )
            case04.details = {
                'version_before': version_before_reindex,
                'version_after': new_version,
            }
            if not case04.ok:
                case04.error = 'version did not increment or status not indexed'
        except Exception as exc:  # noqa: BLE001
            case04.error = str(exc)
    else:
        case04.error = f'HTTP {status}: {body}'
    results.append(case04)

    # UAT-RAG-05 — delete document
    case05 = CaseResult('UAT-RAG-05', 'DELETE document removes row')
    status, body = _request_json('DELETE', f'{api}/documents/{doc_id}')
    if status == 200:
        check_status, check_body = _request_json('GET', f'{api}/documents/{doc_id}')
        case05.ok = check_status == 404
        case05.details = {'get_after_delete': check_status}
        if not case05.ok:
            case05.error = f'expected 404, got {check_status}: {check_body}'
    else:
        case05.error = f'HTTP {status}: {body}'
    results.append(case05)

    # UAT-RAG-06 — delete entity cascades documents
    case06 = CaseResult('UAT-RAG-06', 'DELETE entity cascades documents')
    cascade_entity_id = entity_id
    cascade_doc_id: str | None = None
    status, upload_body = _multipart_upload(
        f'{api}/documents/upload',
        fields={
            'entity_id': cascade_entity_id,
            'title': f'UAT cascade {suffix}',
        },
        file_field='file',
        file_path=SAMPLE_PDF,
        filename='sample-guide.pdf',
    )
    if status == 201 and isinstance(upload_body, dict):
        cascade_doc_id = str(upload_body['doc_id'])
    status, body = _request_json('DELETE', f'{api}/entities/{cascade_entity_id}')
    if status == 200 and cascade_doc_id:
        check_status, check_body = _request_json(
            'GET',
            f'{api}/documents/{cascade_doc_id}',
        )
        case06.ok = check_status == 404
        case06.details = {
            'entity_id': cascade_entity_id,
            'doc_id': cascade_doc_id,
            'get_doc_after_entity_delete': check_status,
        }
        if not case06.ok:
            case06.error = f'expected 404, got {check_status}: {check_body}'
        entity_id = None
    else:
        case06.error = f'HTTP {status}: {body} (upload={upload_body})'
    results.append(case06)

    return results


def _write_results(base: str, results: list[CaseResult]) -> None:
    lines = [f'UAT RAG DEV-507 — base={base}', '']
    for result in results:
        mark = 'PASS' if result.ok else 'FAIL'
        lines.append(f'[{mark}] {result.case_id}: {result.description}')
        if result.details:
            lines.append(f'  details: {json.dumps(result.details, ensure_ascii=False)}')
        if result.error:
            lines.append(f'  error: {result.error}')
        lines.append('')
    passed = sum(1 for item in results if item.ok)
    pct = round(100 * passed / len(results)) if results else 0
    lines.append(f'SUMMARY: {passed}/{len(results)} PASS ({pct}%)')
    RESULTS_FILE.write_text('\n'.join(lines), encoding='utf-8')


def main() -> int:
    _load_env()
    print(f'UAT RAG DEV-507 — base={BASE}\n')
    if not SAMPLE_PDF.is_file():
        print(f'ERROR: missing {SAMPLE_PDF}')
        return 1

    try:
        results = run_battery(BASE)
    except Exception as exc:  # noqa: BLE001
        print(f'ERROR: {exc}')
        return 1

    for index, result in enumerate(results, 1):
        status = 'PASS' if result.ok else 'FAIL'
        print(f'[{index}/{len(results)}] {result.case_id}: {status}')
        if result.details:
            print(f'  details: {result.details}')
        if result.error:
            print(f'  error: {result.error}')
        print()

    passed = sum(1 for item in results if item.ok)
    pct = round(100 * passed / len(results)) if results else 0
    threshold_ok = pct >= 80 and passed >= 5
    print('=' * 60)
    print(f'RESULTAT: {passed}/{len(results)} PASS ({pct}%)')
    print(f'Umbral DEV-507: >=80% i >=5 casos -> {"OK" if threshold_ok else "KO"}')
    print('=' * 60)
    for result in results:
        mark = 'OK' if result.ok else 'KO'
        print(f'  [{mark}] {result.case_id}')

    try:
        _write_results(BASE, results)
        print(f'\nResultats escrits a {RESULTS_FILE}')
    except OSError as exc:
        print(f'\nWARN: no s\'ha pogut escriure {RESULTS_FILE}: {exc}')

    return 0 if threshold_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
