## Objetivo

Crear el **widget de xat** (globus fix + panell overlay) com a assets portables per incrustar al layout PHP de femturisme.cat, reutilitzant la lògica SSE de `chat.js`.

## Contexto

- Fase 3 tancada: API `/api/chat` i `/api/session/reset` funcionals.
- `app/static/js/chat.js` és una demo full-page; cal adaptar-la a widget flotant (tecnic §4.7).
- El PHP del portal inclourà JS/CSS des d'aquest repo o CDN staging; **no** cal codi PHP aquí.
- Prerequisit per issues #2–#3 del batch (context i reset al widget).

## Alcance

| In | Fuera |
|----|-------|
| Globus + panell overlay (obrir/tancar, conservar sessió) | Reverse proxy (issue separada) |
| `chat-widget.js` + `widget.css` (+ HTML snippet include) | `page_context` al body (issue api/widget-context) |
| Markdown amb `marked`, enllaços `target="_blank"` | Mode entitat / RAG |
| Demo local o pàgina static de prova al repo | Codi PHP del CMS client |

## Criterios de aceptación

- [ ] Globus visible cantó inferior dret; clic obre panell; tancar amaga panell sense perdre `session_id`
- [ ] POST `/api/chat` via fetch + ReadableStream SSE (mateix patró que `chat.js`)
- [ ] Events `tool_call`, `tool_result`, `text_chunk`, `done` renderitzats al panell
- [ ] CSS responsive (panell usable en viewport mòbil ~375px)
- [ ] Snippet/document «com incloure al PHP» a `docs/devs/` o comentari al HTML
- [ ] `pytest -v` sense regressions (cap canvi trencador a API)

## Capas / archivos principales

- `app/static/js/chat-widget.js` (nou, extret/adaptat de `chat.js`)
- `app/static/css/widget.css` (nou)
- `app/templates/` o `docs/devs/widget-php-include.md` — fragment HTML
- Opcional: ruta demo Flask per provar widget abans de PHP

## Issues relacionadas

- `api-page-agent-context.md` (següent)
- `widget-context-reset.md` (després de API context)
- `php-proxy-docs.md`

## Verificación

```powershell
python -m pytest -v
python main.py
# Obrir demo widget; enviar missatge; comprovar SSE i Markdown
```

## Referencias

- [plan-fase4-php-widget.md](../devs/plan-fase4-php-widget.md)
- [tecnic.md](../client/tecnic.md) §4.7
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-400
