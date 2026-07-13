## Objetivo

Tancar la validació **UAT del widget** en staging: checklist desktop/mòbil, integració end-to-end amb proxy i context de pàgina.

## Contexto

- Depèn de les issues anteriors del batch Fase 4 (widget, API context, proxy docs).
- DEV-405 / T-PHP-06 (checklist): proves responsive i flux real staging.
- Part del treball és **documentació + execució manual** amb l'equip PHP/client.

## Alcance

| In | Fuera |
|----|-------|
| Checklist UAT desktop + mòbil (375px, 768px, desktop) | Sign-off client formal (DEV-606) |
| Matriu proves: obrir globus, xat, reset, enllaços Markdown | Mode entitat |
| Evidència mínima (captures o notes) a doc | Automatització Playwright |
| Actualitzar `testing.md` o secció UAT widget | Producció femturisme.cat |

## Criterios de aceptación

- [ ] Checklist UAT completada amb ≥ casos crítics OK (obrir, enviar, SSE, reset, tancar panell)
- [ ] Desktop i mòbil verificats (layout no trencat, scroll panell)
- [ ] Same-origin confirmat (cap error CORS al navegador)
- [ ] `page_context` de prova (p.ex. secció agenda) millora resposta en cas ambigu documentat
- [ ] Resultats registrats a `docs/devs/uat-widget-staging.md`

## Capas / archivos principales

- `docs/devs/uat-widget-staging.md` (nou)
- `docs/devs/testing.md` (enllaç)
- `docs/devs/plan-fase4-php-widget.md` (marcat complet al tancar)

## Issues relacionadas

- Totes les issues Fase 4 del manifest

## Verificación

```powershell
python -m pytest -v
# Manual staging: checklist UAT desktop + mobil
```

## Referencias

- [tecnic.md](../client/tecnic.md) §14.5 (si existeix secció PHP)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-405
