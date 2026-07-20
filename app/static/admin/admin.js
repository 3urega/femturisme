/* Admin guides UI — consumes /admin/api/* with Bearer token (issue #32). */
const AdminGuides = (() => {
  const TOKEN_KEY = 'femturisme_admin_api_token';
  const API_PREFIX = '/admin/api';
  const POLL_STATUSES = new Set(['pending', 'extracting', 'chunking', 'embedding']);
  const POLL_MS = 3000;

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY) || '';
  }

  function setToken(value) {
    if (value) {
      sessionStorage.setItem(TOKEN_KEY, value);
    } else {
      sessionStorage.removeItem(TOKEN_KEY);
    }
  }

  function showError(message) {
    const el = document.getElementById('admin-alert');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('d-none');
  }

  function clearError() {
    const el = document.getElementById('admin-alert');
    if (!el) return;
    el.textContent = '';
    el.classList.add('d-none');
  }

  async function apiFetch(path, options = {}) {
    clearError();
    const headers = new Headers(options.headers || {});
    const token = getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_PREFIX}${path}`, {
      ...options,
      headers,
    });

    let payload = null;
    const text = await response.text();
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (_err) {
        payload = { error: text };
      }
    }

    if (!response.ok) {
      const message = (payload && payload.error) || `HTTP ${response.status}`;
      throw new Error(message);
    }
    return payload;
  }

  function statusBadgeClass(status) {
    return `badge status-badge-${status || 'pending'}`;
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString('ca-ES');
  }

  function bindTokenButton() {
    const btn = document.getElementById('admin-token-btn');
    if (!btn) return;
    btn.addEventListener('click', () => {
      const current = getToken();
      const next = window.prompt('Admin API token (Bearer):', current);
      if (next === null) return;
      setToken(next.trim());
      window.location.reload();
    });
  }

  async function loadDocuments() {
    const data = await apiFetch('/documents');
    return data.documents || [];
  }

  async function loadEntities() {
    const data = await apiFetch('/entities');
    return data.entities || [];
  }

  function renderDocumentsTable(documents) {
    const tbody = document.getElementById('guides-table-body');
    if (!tbody) return;

    if (!documents.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">Cap document encara.</td></tr>';
      return;
    }

    tbody.innerHTML = documents.map((doc) => {
      const detailUrl = `/admin/guides/${doc.doc_id}`;
      return `
        <tr>
          <td>${escapeHtml(doc.title || '—')}</td>
          <td><code>${escapeHtml(doc.entity_id || '')}</code></td>
          <td><span class="${statusBadgeClass(doc.status)}">${escapeHtml(doc.status || 'pending')}</span></td>
          <td>${doc.chunks_count ?? 0}</td>
          <td>${formatDate(doc.updated_at || doc.indexed_at)}</td>
          <td><a href="${detailUrl}">Detall</a></td>
        </tr>
      `;
    }).join('');
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;');
  }

  async function initListPage() {
    bindTokenButton();
    try {
      const documents = await loadDocuments();
      renderDocumentsTable(documents);
    } catch (err) {
      showError(err.message || String(err));
      renderDocumentsTable([]);
    }
  }

  async function initUploadPage() {
    bindTokenButton();
    const select = document.getElementById('entity_id');
    const form = document.getElementById('upload-form');
    if (!select || !form) return;

    try {
      const entities = await loadEntities();
      if (!entities.length) {
        select.innerHTML = '<option value="">Cap entitat — crea-ne una via API</option>';
      } else {
        select.innerHTML = [
          '<option value="">Selecciona entitat…</option>',
          ...entities.map((entity) => (
            `<option value="${entity.entity_id}">${escapeHtml(entity.name)} (${escapeHtml(entity.entity_type)})</option>`
          )),
        ].join('');
      }
    } catch (err) {
      showError(err.message || String(err));
      select.innerHTML = '<option value="">Error carregant entitats</option>';
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      clearError();
      const formData = new FormData(form);
      try {
        const created = await apiFetch('/documents/upload', {
          method: 'POST',
          body: formData,
        });
        window.location.href = `/admin/guides/${created.doc_id}`;
      } catch (err) {
        showError(err.message || String(err));
      }
    });
  }

  function renderDocumentDetail(doc) {
    document.getElementById('doc-title').textContent = doc.title || 'Document';
    const statusEl = document.getElementById('doc-status');
    statusEl.textContent = doc.status || 'pending';
    statusEl.className = statusBadgeClass(doc.status);
    document.getElementById('doc-version').textContent = doc.version != null ? `v${doc.version}` : '';
    document.getElementById('doc-entity-id').textContent = doc.entity_id || '—';
    document.getElementById('doc-filename').textContent = doc.source_filename || '—';
    document.getElementById('doc-pages').textContent = doc.pages_count ?? 0;
    document.getElementById('doc-chunks').textContent = doc.chunks_count ?? 0;
    document.getElementById('doc-embedded').textContent = doc.embedded_chunks_count ?? 0;
    document.getElementById('doc-indexed-at').textContent = formatDate(doc.indexed_at);

    const errorEl = document.getElementById('doc-error');
    if (doc.status === 'failed' && doc.error_message) {
      errorEl.textContent = doc.error_message;
      errorEl.classList.remove('d-none');
    } else {
      errorEl.textContent = '';
      errorEl.classList.add('d-none');
    }

    const smokeBtn = document.getElementById('smoke-btn');
    if (smokeBtn) {
      smokeBtn.disabled = doc.status !== 'indexed';
    }
  }

  function renderSmokeResults(payload) {
    const container = document.getElementById('smoke-results');
    if (!container) return;
    const results = payload.results || [];
    if (!results.length) {
      container.innerHTML = '<p class="text-muted mb-0">Cap fragment retornat.</p>';
      return;
    }
    container.innerHTML = results.map((hit) => `
      <div class="smoke-hit">
        <div class="fw-semibold">${escapeHtml(hit.source || 'Fragment')}${hit.page ? ` · p.${hit.page}` : ''}</div>
        <div class="small text-muted mb-1">${escapeHtml(hit.summary || '')}</div>
        <div>${escapeHtml(hit.content || '')}</div>
      </div>
    `).join('');
  }

  async function pollDocument(docId) {
    const doc = await apiFetch(`/documents/${docId}`);
    renderDocumentDetail(doc);
    if (POLL_STATUSES.has(doc.status)) {
      setTimeout(() => pollDocument(docId), POLL_MS);
    }
    return doc;
  }

  async function initDetailPage(docId) {
    bindTokenButton();
    const reindexBtn = document.getElementById('reindex-btn');
    const smokeBtn = document.getElementById('smoke-btn');

    try {
      await pollDocument(docId);
    } catch (err) {
      showError(err.message || String(err));
    }

    if (reindexBtn) {
      reindexBtn.addEventListener('click', async () => {
        clearError();
        reindexBtn.disabled = true;
        try {
          await apiFetch(`/documents/${docId}/reindex`, { method: 'POST' });
          await pollDocument(docId);
        } catch (err) {
          showError(err.message || String(err));
        } finally {
          reindexBtn.disabled = false;
        }
      });
    }

    if (smokeBtn) {
      smokeBtn.addEventListener('click', async () => {
        clearError();
        const queryInput = document.getElementById('smoke-query');
        const query = (queryInput && queryInput.value.trim()) || '';
        if (!query) {
          showError('Introdueix una consulta de prova.');
          return;
        }
        smokeBtn.disabled = true;
        try {
          const payload = await apiFetch(`/documents/${docId}/smoke-test`, {
            method: 'POST',
            body: JSON.stringify({ query }),
          });
          renderSmokeResults(payload);
        } catch (err) {
          showError(err.message || String(err));
        } finally {
          smokeBtn.disabled = false;
        }
      });
    }
  }

  return {
    initListPage,
    initUploadPage,
    initDetailPage,
  };
})();
