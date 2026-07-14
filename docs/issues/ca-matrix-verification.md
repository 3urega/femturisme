## Objetivo

Completar la **matriz CA-01…CA-09** con evidencia reproducible en el chat Flask (DEV-605), cerrando la verificación funcional de Fase producto 1 sin PHP.

## Contexto

- UAT catálogo (**DEV-604**, 12/12 routing) e idiomas (**DEV-601**, 7/8) ya ejecutados.
- Fase 4 pospuesta: la evidencia se genera contra `http://127.0.0.1:5010/`.
- CA-07 (contexto) depende de `uat-conversation-context.md`.

## Alcance

| In | Fuera |
|----|-------|
| Documento `docs/devs/ca-matrix-fase1.md` con tabla CA + evidencia + comando/script | Sign-off formal cliente (DEV-606) |
| Enlazar scripts UAT existentes (`uat_catalog_battery`, `uat_languages_battery`, `uat_context_battery`) | UAT responsive PHP (DEV-405) |
| Gaps identificados → issues nuevas o fixes puntuales | RAG / mode entitat (Fase 7) |
| Actualizar checklist DEV-605 si ≥8/9 CA verificados | Despliegue producción (DEV-607) |

## Criterios de aceptación

- [ ] Matriz con filas **CA-01…CA-09**: descripción, estado (OK/KO/parcial), evidencia (script, fecha, nota)
- [ ] CA-01…CA-06: referencia a UAT catálogo + prueba manual breve documentada
- [ ] CA-07: referencia a `uat_context_battery.py` con resultado ≥80%
- [ ] CA-08: evidencia (respuesta sin datos inventados en caso `total=0`)
- [ ] CA-09: evidencia arquitectura (6 tools parametrizadas, sin text-to-SQL)
- [ ] Checklist `DEV-605` marcado si criterio Detect cumplido
- [ ] Issues abiertas solo para CA en estado KO con plan de fix

## Capas / archivos principales

- `docs/devs/ca-matrix-fase1.md` (nuevo)
- `docs/devs/checklist-entrega.md` — DEV-605
- `scripts/uat_catalog_battery.py`, `scripts/uat_languages_battery.py`, `scripts/uat_context_battery.py`

## Issues relacionadas

- `uat-conversation-context.md`
- `rate-limiting-logging.md`
- `sql-mapeo-completion.md`

## Verificación

```powershell
python scripts/uat_catalog_battery.py
python scripts/uat_languages_battery.py
python scripts/uat_context_battery.py
# Revisar docs/devs/ca-matrix-fase1.md completo
```

## Referencias

- [requeriments.md](../client/requeriments.md) §12 (CA-01…CA-09)
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-605, DEV-606
