# Guia per a desenvolupadors PHP — Globus de xat (Fase 4)

Document orientatiu per l'equip que manté **femturisme.cat** (CMS PHP). Descriu què cal implementar al portal, què fa el servei Python i com verificar-ho abans de producció.

**Estat:** l'agent Python ja té API de xat estable; **tocar el layout PHP i el proxy** (checklist `DEV-400`…`DEV-406`).  
**Issues GitHub:** [#18](https://github.com/3urega/femturisme/issues/18) (globus) … [#22](https://github.com/3urega/femturisme/issues/22) (UAT staging).

---

## 1. Resum executiu

| Qui | Responsabilitat |
|-----|-----------------|
| **Equip PHP (vosaltres)** | Globus + panell al layout global, reverse proxy same-origin, injectar `page_context` / `agent_context`, botó «Nova conversa», proves responsive |
| **Servei Python (agent)** | Lògica de l'agent, buscadors MySQL, SSE, historial de sessió, rate limiting |
| **Ops** | Xarxa PHP → Python, `.env`, firewall, staging (**DEV-027**) |

El navegador **mai** ha de cridar directament el host de l'agent. Totes les peticions van a **`https://www.femturisme.cat/api/...`** i el servidor web fa de proxy cap al Flask.

---

## 2. Arquitectura (obligatori entendre-ho)

```text
Visitant (navegador)
    │  POST /api/chat          (same-origin, sense CORS)
    │  POST /api/session/reset
    ▼
femturisme.cat (nginx/Apache + PHP)
    │  reverse proxy
    ▼
Servei agent Python (Flask)
    │  MySQL read-only (catàleg)
    └── PostgreSQL (RAG — no actiu al xat públic Fase 1)
```

**ADR-008:** same-origin. No configureu CORS al navegador com a solució; el proxy ha de reenviar el cos i mantenir **SSE** sense bufferitzar.

Referència: [tecnic.md §4.8](../client/tecnic.md), issue [#21](https://github.com/3urega/femturisme/issues/21).

---

## 3. Què inclou la Fase 4 (i què no)

### Inclòs ara (Fase producte 1)

- Globus fix + panell overlay al web públic.
- Xat en **mode femturisme** (catàleg MySQL: agenda, rutes, establiments, etc.).
- Idiomes: l'agent respon en l'idioma de la pregunta (ca / es / en; francès segons requeriments).
- Enllaços a pàgines de femturisme.cat a les respostes.
- Context de pàgina opcional (`page_context`) per desambiguar («què fer aquí?»).

### Encara fora d'abast (no implementar al widget públic encara)

| Tema | Motiu |
|------|--------|
| **Mode entitat** (`agent_context.mode = "entitat"`) | Fase 2; l'API retorna **501** avui |
| **RAG / guies PDF** al xat de femturisme.cat | Fase 2; Fase 1 = només catàleg MySQL ([requeriments.md §4](../client/requeriments.md)) |
| Pujar PDFs o panell admin RAG | Servei Python `/admin/guides*` — xarxa interna, no CMS PHP |
| Gestor d'entitats al backoffice PHP | **DEV-506** / RF-13 — batch posterior |
| Editar contingut CMS des del xat | Fora d'abast explícit |

---

## 4. Tasques PHP (mapatge checklist)

| ID | Tasca | Detect |
|----|-------|--------|
| **DEV-400** | Globus + panell al layout global (T-PHP-01) | Widget visible a staging |
| **DEV-401** | Reverse proxy `/api/chat` i `/api/session/reset` (T-PHP-02) | Peticions same-origin OK |
| **DEV-402** | Enviar `page_context` al body (T-PHP-03) | Camp present segons URL |
| **DEV-403** | `agent_context` per defecte mode femturisme (T-PHP-04) | `{ "mode": "femturisme", "entity_id": null }` |
| **DEV-404** | Botó «Nova conversa» → `/api/session/reset` (T-PHP-05) | Historial netejat |
| **DEV-405** | Proves desktop + mòbil (T-PHP-06) | Checklist §14.5 |
| **DEV-406** | Headers SSE proxy (`X-Accel-Buffering: no`, timeout) | Stream no es talla |

La part d'API (`page_context` / `agent_context`) ja està al Python ([#19](https://github.com/3urega/femturisme/issues/19) tancada). **Us toca connectar el widget i el proxy.**

---

## 5. Assets JavaScript i CSS

### Referència actual (demo Python)

Al repo de l'agent hi ha una demo **pàgina sencera** (no globus):

| Fitxer | Ús |
|--------|-----|
| [`app/static/js/chat.js`](../../app/static/js/chat.js) | Client SSE + Markdown — **patró a seguir** |
| [`app/static/css/style.css`](../../app/static/css/style.css) | Estils demo full-page |
| [`app/templates/index.html`](../../app/templates/index.html) | Estructura HTML de referència |

**Dependències del client (CDN demo):**

- [marked](https://cdn.jsdelivr.net/npm/marked@15/marked.min.js) — render Markdown a les respostes
- Font Awesome (opcional, icones)
- **No** cal Bootstrap al widget mínim si preferiu CSS propi

### Widget globus (objectiu)

Issue [#18](https://github.com/3urega/femturisme/issues/18): es publicaran assets portables (`chat-widget.js`, `widget.css`) adaptats de `chat.js`. Fins llavors podeu:

1. **Opció A (recomanada):** esperar o copiar des del repo agent quan estiguin a `main`.
2. **Opció B:** adaptar vosaltres `chat.js` a overlay (globus + panell) mantenint la mateixa lògica SSE.

### Especificació UI ([tecnic.md §4.7](../client/tecnic.md))

- Globus **fix cantó inferior dret**.
- Clic obre **panell overlay**; tancar amaga el panell **sense perdre** `session_id`.
- Enllaços de les respostes: **`target="_blank"`** + `rel="noopener"`.
- Panell usable en mòbil (~375px d'amplada).

---

## 6. Com incloure al layout PHP

### 6.1 Fragment HTML (esquelet)

Incloure **abans de `</body>`** al layout global (totes les pàgines públiques):

```html
<!-- femturisme chat widget -->
<div id="ft-chat-root">
  <button type="button" id="ft-chat-toggle" aria-label="Obrir assistent" aria-expanded="false">
    <!-- icona globus -->
  </button>
  <div id="ft-chat-panel" hidden>
    <header>
      <span>Assistent femturisme</span>
      <button type="button" id="ft-chat-close" aria-label="Tancar">×</button>
    </header>
    <div id="chat-messages"><!-- missatge benvinguda --></div>
    <div class="chat-input-area">
      <textarea id="chat-input" rows="1" maxlength="2000"></textarea>
      <button type="button" id="btn-send">Enviar</button>
    </div>
    <button type="button" id="btn-reset">Nova conversa</button>
  </div>
</div>
```

Els `id` han de coincidir amb el JS del widget (o adaptar el JS als vostres `id`).

### 6.2 Config injectada des de PHP

Definiu una config global **abans** de carregar el JS del widget:

```html
<script>
  window.FEMTURISME_CHAT_CONFIG = {
    page_context: {
      section: <?= json_encode($section ?? null) ?>,
      ubicacio: <?= json_encode($ubicacio ?? null) ?>,
      municipality: <?= json_encode($municipality ?? null) ?>
    },
    agent_context: {
      mode: 'femturisme',
      entity_id: null
    }
  };
</script>
<script src="/assets/js/chat-widget.js"></script>
<link rel="stylesheet" href="/assets/css/widget.css">
```

**Important:** ompliu `page_context` segons la pàgina actual del CMS (vegeu §8). Si no teniu dades, podeu ometre camps o passar `{}` — l'API accepta l'absència de context.

### 6.3 URLs relatives

El JS ha d'usar **rutes relatives** al domini del portal:

```javascript
fetch('/api/chat', { method: 'POST', ... })
fetch('/api/session/reset', { method: 'POST', ... })
```

No hardcodeu `http://127.0.0.1:5010` ni el host de l'agent al JavaScript de producció.

---

## 7. Reverse proxy (DEV-401, DEV-406)

### Nginx (exemple)

```nginx
location /api/chat {
    proxy_pass http://<HOST_AGENT>:<PORT>/api/chat;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_read_timeout 300s;
    add_header X-Accel-Buffering no;
}

location /api/session/reset {
    proxy_pass http://<HOST_AGENT>:<PORT>/api/session/reset;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

Substituïu `<HOST_AGENT>` i `<PORT>` per staging/prod (ops us ho passarà; dev agent sovint `:5010` o `:5080` en Docker).

### Errors habituals

| Síntoma | Causa probable |
|---------|----------------|
| La resposta arriba tota al final (no streaming) | `proxy_buffering on` o falta `X-Accel-Buffering: no` |
| Timeout al mig d'una resposta llarga | `proxy_read_timeout` massa baix |
| CORS al navegador | El JS apunta a un altre domini; cal proxy same-origin |
| 502 Bad Gateway | Python aturat o xarxa PHP→agent tancada (**DEV-027**) |

Smoke test des del servidor (o staging):

```bash
curl -N -X POST https://staging.femturisme.cat/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","session_id":"smoke-test"}'
```

Heu de veure línies `data: {"type":"text_chunk",...}` i acabar amb `data: {"type":"done",...}`.

---

## 8. Contracte API (el widget ha de respectar-lo)

Font completa: [tecnic.md §9.1–9.2](../client/tecnic.md).

### POST `/api/chat`

**Request JSON:**

| Camp | Obligatori | Descripció |
|------|------------|------------|
| `message` | Sí | Text usuari (no buit) |
| `session_id` | No | UUID; si falta, el servidor en genera un |
| `page_context` | No | Objecte amb context de pàgina |
| `agent_context` | No | Mode operatiu (default femturisme) |

**Exemple:**

```json
{
  "message": "Què fer aquí?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "page_context": {
    "section": "agenda",
    "ubicacio": "Empordà",
    "municipality": "Pals"
  },
  "agent_context": {
    "mode": "femturisme",
    "entity_id": null
  }
}
```

**`page_context` — camps reconeguts avui:**

| Camp | Exemple | Quan omplir-lo (PHP) |
|------|---------|----------------------|
| `section` | `"agenda"`, `"rutes"`, `"destinacions"` | Tipus de secció / plantilla de la pàgina |
| `ubicacio` | `"Empordà"`, `"Berguedà"` | Comarca o àrea territorial de la fitxa |
| `municipality` | `"Pals"`, `"Berga"` | Municipi si la pàgina n'és d'un |

No cal inventar camps nous sense acordar-ho amb l'equip agent; el parser Python només accepta aquests tres.

**Response:** `Content-Type: text/event-stream` (SSE sobre POST + `fetch` + `ReadableStream` — **no** useu `EventSource` perquè només fa GET).

**Events SSE:**

| `type` | Acció al UI |
|--------|-------------|
| `tool_call` | Mostrar indicador «cercant…» (opcional) |
| `tool_result` | Marcar cerca completada |
| `text_chunk` | Anar afegint text; render Markdown incremental |
| `done` | Tancar torn; `full_text` disponible |
| `error` | Mostrar missatge d'error |

Patró d'implementació: veure [`chat.js`](../../app/static/js/chat.js) funcions `_send`, `_handleEvent`.

**Errors HTTP:**

| Codi | Significat |
|------|------------|
| 400 | `message` buit o JSON invàlid (`page_context` / `agent_context` mal format) |
| 501 | `agent_context.mode = "entitat"` — encara no disponible al portal |
| 500 | Error intern agent |

### POST `/api/session/reset`

```json
{ "session_id": "<mateix uuid que sessionStorage>" }
```

Response: `{ "ok": true }`.

**Botó «Nova conversa» (DEV-404):**

1. Cridar `/api/session/reset` amb el `session_id` actual.
2. Esborrar o regenerar `session_id` a `sessionStorage` (veure `chat.js`).
3. Netejar missatges del panell (deixar només benvinguda).
4. No cal recarregar tota la pàgina si el widget ho gestiona bé (la demo Flask fa `reload()` — evitable).

### Sessió (`session_id`)

- Guardar a **`sessionStorage`** (clau recomanada: `chat_session_id`).
- Generar amb `crypto.randomUUID()` si no existeix.
- Mantenir la mateixa sessió en tancar/obrir el panell (globus).
- Només canviar en «Nova conversa» o nova pestanya del navegador.

---

## 9. Comportament esperat de l'agent (per validar UAT)

Al **mode femturisme** (Fase 1), l'assistent:

- Consulta el **catàleg MySQL** (6 buscadors): establiments, articles, destinacions, rutes, agenda, experiències promocionals.
- **No** consulta guies PDF / RAG encara que existeixin al sistema.
- Inclou **enllaços** `https://www.femturisme.cat/...` quan hi ha resultats.
- Respon en l'**idioma de la pregunta**.

Preguntes de prova útils (staging):

- «Quins esdeveniments hi ha a l'Empordà aquest cap de setmana?»
- «On dormir al Berguedà?»
- «Rutes de senderisme familiars a Catalunya»

---

## 10. Checklist abans de donar per bo (DEV-405)

Reutilitza [tecnic.md §14.5](../client/tecnic.md):

- [ ] Globus visible a **home** i pàgines interiors.
- [ ] Obrir/tancar panell sense perdre conversa.
- [ ] Enviar missatge → resposta amb streaming visible.
- [ ] Enllaços obren en nova pestanya.
- [ ] «Nova conversa» reseteja historial.
- [ ] `page_context` coherent en una pàgina d'agenda / destinació / municipi (comproveu al body de la petició al DevTools).
- [ ] **Desktop:** Chrome, Firefox, Edge.
- [ ] **Mòbil:** Safari iOS, Chrome Android (~375px).
- [ ] Proxy **sense errors CORS** (Network tab: requests a `/api/chat` same-origin).
- [ ] Cap secret (API keys LLM, tokens admin) al JS del portal.

---

## 11. Coordinació amb l'equip agent

| Necessitat | Contacte / on |
|------------|----------------|
| URL host agent staging | Ops / **DEV-027** |
| Healthcheck agent | `GET /health` al host agent (via proxy opcional) |
| Canvis API o nous camps `page_context` | Issue al repo `3urega/femturisme` |
| Assets widget actualitzats | Repo agent `app/static/js/`, `app/static/css/` |
| Panell admin PDF (intern) | **No** és part del globus públic — `/admin/guides` al servei Python |

---

## 12. Referències

| Document | Contingut |
|----------|-----------|
| [tecnic.md §4.7–4.9, §9, §14.5](../client/tecnic.md) | Widget, proxy, API, tests PHP |
| [funcional.md §8, §13–15](../client/funcional.md) | Fonts, modes operatius, gestor documental |
| [requeriments.md §4](../client/requeriments.md) | Fase 1 vs Fase 2, sense RAG al portal |
| [dominio-femturisme-ca.md §5](../client/dominio-femturisme-ca.md) | 6 buscadors de catàleg |
| [plan-fase4-php-widget.md](plan-fase4-php-widget.md) | Pla batch, issues #18–#22 |
| [checklist-entrega.md](checklist-entrega.md) | DEV-400…406 |
| Demo local agent | `python main.py` → http://127.0.0.1:5010/ (xat prova, no globus) |

---

**Última actualització:** 2026-07-20 — redacció inicial per inici Fase 4 (globus PHP).
