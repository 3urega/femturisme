## Objetivo

Connectar el widget amb **`page_context`**, **`agent_context`** (defaults femturisme) i el botó **Nova conversa** (`POST /api/session/reset`).

## Contexto

- Depèn de `widget-globus-assets.md` (UI) i `api-page-agent-context.md` (API).
- El PHP del client injectarà config via `window.FEMTURISME_CHAT_CONFIG` o `data-*` al layout.
- `chat.js` demo ja crida `/api/session/reset`; cal portar-ho al widget amb la mateixa semàntica.

## Alcance

| In | Fuera |
|----|-------|
| Init widget des de config global (`page_context`, `agent_context`) | Codi PHP que genera la config per URL |
| Enviar context en cada `POST /api/chat` | Mode entitat actiu |
| Botó «Nova conversa» → reset + neteja UI | Proxy nginx (issue php-proxy-docs) |
| Documentar contracte config per equip PHP | Tests E2E al CMS real |

## Criterios de aceptación

- [ ] `FEMTURISME_CHAT_CONFIG.page_context` s'envia al body del xat quan existeix
- [ ] Per defecte `agent_context: { mode: "femturisme", entity_id: null }` si PHP no passa res
- [ ] Botó reset crida `/api/session/reset` amb `session_id` i buida missatges (excepte benvinguda)
- [ ] Exemple PHP/JS a `docs/devs/widget-php-include.md` actualitzat
- [ ] `pytest -v` verd; smoke manual widget + API context

## Capas / archivos principales

- `app/static/js/chat-widget.js`
- `docs/devs/widget-php-include.md`
- `tests/api/test_chat.py` (opcional ampliació amb context al mock)

## Issues relacionadas

- `widget-globus-assets.md`
- `api-page-agent-context.md`
- `php-proxy-docs.md`

## Verificación

```powershell
python -m pytest -v
python main.py
# Config de prova: page_context Empordà; missatge ambigu; reset sessió
```

## Referencias

- [tecnic.md](../client/tecnic.md) §4.9
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-404
