## Objetivo

Panell admin Flask mínim per operar entitats i PDFs, més bateria UAT interna RAG. Tanca **DEV-507**.

## Contexto

- Operadors femturisme necessiten UI sense tocar el CMS PHP (DEV-506 queda fora).
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9: `/admin/guides` — llista, pujada, detall, reindexar.
- El xat públic continua **sense RAG** (DEV-600); aquest UAT és admin + smoke-test, no widget visitant.

## Alcance

| In | Fuera |
|----|-------|
| HTML+JS a `app/static/admin/` + templates Flask | React, backoffice PHP |
| Pantalles: llista entitats, llista documents, formulari pujada, detall document (estat, reindexar, smoke-test) | Auth producció completa (v1: token header o basic config) |
| `scripts/uat_rag_battery.py` + `uat_rag_battery_results.txt` | UAT mode entitat al widget (Fase 7) |
| Protecció ruta `/admin/*` (mínim) | DEV-506 |

## Criterios de aceptación

- [ ] `GET /admin/guides` mostra documents amb badge d'estat (`pending`…`indexed`/`failed`)
- [ ] Formulari pujada crea document i dispara indexació; detall mostra error si `failed`
- [ ] Botó Reindexar crida API i actualitza estat
- [ ] Smoke-test des del panell retorna fragments i es mostren a la UI
- [ ] UAT intern: ≥5 proves (crear entitat, pujar PDF, indexar, cercar, reindexar) documentades; ≥80% PASS
- [ ] Checklist **DEV-507** marcat

## Capas / archivos principales

- `app/routes/admin.py` — rutas HTML
- `app/templates/admin/` (guides_list.html, guides_upload.html, guides_detail.html)
- `app/static/admin/admin.js`, `admin.css`
- `scripts/uat_rag_battery.py`

## Issues relacionadas

- `rag-search-entity-knowledge.md` (prerequisit)
- Totes les issues `rag-*.md` del batch

## Verificación

```powershell
python scripts/uat_rag_battery.py
# Manual: http://127.0.0.1:5010/admin/guides
```

## Referencias

- [tecnic.md](../client/tecnic.md) §14.4 (UAT admin RAG)
- [plan-integracion-ca.md](../plan-integracion-ca.md) §9 (frontend admin)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-507
