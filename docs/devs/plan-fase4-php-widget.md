# Pla: Fase 4 — Integració web femturisme.cat

Integrar el xat al portal públic via **widget JS/CSS portable**, suport API per **page_context** i **agent_context**, documentació de **reverse proxy same-origin** i checklist **UAT responsive**.

**Prerequisit tancat:** Fase 3 batch 2 ([#12](https://github.com/3urega/femturisme/issues/12)…[#17](https://github.com/3urega/femturisme/issues/17)) — 6 buscadors MySQL + tests integració.

**Estat:** publicat a GitHub ([#18](https://github.com/3urega/femturisme/issues/18)…[#22](https://github.com/3urega/femturisme/issues/22), 2026-07-13) · Manifest: [manifest.fase4-php.json](../issues/manifest.fase4-php.json)

---

## Objectiu

| Què | Per què |
|-----|---------|
| Widget globus + panell overlay | DEV-400 — T-PHP-01; reutilitzar SSE de `chat.js` |
| API `page_context` + `agent_context` | DEV-402, DEV-403 — context operatiu Fase 1 |
| Widget envia context + reset sessió | DEV-404 — T-PHP-04/05 (checklist) |
| Docs proxy SSE same-origin | DEV-401, DEV-406 — nginx/apache, headers |
| UAT staging desktop/mòbil | DEV-405 — checklist client |

**Fora d'abast d'aquest batch:** codi PHP del CMS femturisme (repo client); mode entitat / RAG (Fase 5–7); DEV-309 límits operatius (issue futura).

---

## Estat actual (pre-Fase 4)

| Component | Estat |
|-----------|-------|
| `POST /api/chat` SSE | Funcional (demo Flask) |
| `POST /api/session/reset` | Funcional |
| `app/static/js/chat.js` | Demo full-page, sense globus |
| `page_context` / `agent_context` | **No** implementats a API ni agent |
| Reverse proxy | Documentat a `tecnic.md` §4.8; sense guia dev dedicada |
| Layout PHP femturisme.cat | Fora d'aquest repo |

---

## Ordre d'implementació

```text
1. widget-globus-assets        → DEV-400
2. api-page-agent-context      → DEV-402, DEV-403
3. widget-context-reset        → DEV-404 (+ wiring DEV-402)
4. php-proxy-docs              → DEV-401, DEV-406
5. uat-widget-staging          → DEV-405
```

**Nota:** el widget (#1) pot arrencar en paral·lel amb l'API (#2); el wiring de context (#3) depèn d'ambdós.

---

## GitHub issues

| Ordre | GitHub | Slug | Títol | Checklist |
|-------|--------|------|-------|-----------|
| 1 | [#18](https://github.com/3urega/femturisme/issues/18) | `widget-globus-assets.md` | Fase 4: Widget globus JS/CSS portable per PHP | DEV-400 |
| 2 | [#19](https://github.com/3urega/femturisme/issues/19) | `api-page-agent-context.md` | Fase 4: API page_context i agent_context | DEV-402, DEV-403 |
| 3 | [#20](https://github.com/3urega/femturisme/issues/20) | `widget-context-reset.md` | Fase 4: Widget envia context i Nova conversa | DEV-404 |
| 4 | [#21](https://github.com/3urega/femturisme/issues/21) | `php-proxy-docs.md` | Fase 4: Docs reverse proxy SSE same-origin | DEV-401, DEV-406 |
| 5 | [#22](https://github.com/3urega/femturisme/issues/22) | `uat-widget-staging.md` | Fase 4: UAT widget staging desktop i mobil | DEV-405 |

Manifest: [manifest.fase4-php.json](../issues/manifest.fase4-php.json)

---

## Verificació global (post-batch)

```powershell
python -m pytest -v
python main.py
# Manual: obrir widget demo, enviar missatge, reset sessió
# Manual/doc: proxy staging same-origin sense CORS
```

---

## Referències

- [tecnic.md](../client/tecnic.md) §4.7–4.9, §15.4
- [funcional.md](../client/funcional.md) — modes operatius
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md)
- [checklist-entrega.md](checklist-entrega.md) DEV-400…406
