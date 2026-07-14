## Objetivo

Verificar **RF-06 / CA-07**: el agente mantiene el contexto conversacional entre turnos (anáforas, destino/fechas ya indicados) mediante una batería UAT reproducible en el chat Flask.

## Contexto

- La memoria de sesión ya existe (`session_id` + `_history` en `agent_service.py`); falta **evidencia formal** de que funciona en casos reales.
- Requisito explícito en `requeriments.md` (C5, RF-06) y `funcional.md` §9: *«Vull anar al Berguedà» → «On puc dormir allà?»*.
- Bloquea parcialmente **DEV-605** (matriz CA) hasta tener script + resultados.

## Alcance

| In | Fuera |
|----|-------|
| Script `scripts/uat_context_battery.py` con 4–6 escenarios multi-turno | Persistencia Redis/PostgreSQL (P-04) |
| Mismo `session_id` en todos los turnos de un escenario | Perfil de usuario entre sesiones |
| Criterios: tool con `destination` coherente, respuesta sin repetir pregunta al usuario | UAT en portal PHP (Fase 4) |
| Resultados guardados en `scripts/uat_context_battery_results.txt` | Resumen automático de historial largo (truncado tokens) |

## Criterios de aceptación

- [ ] Escenario **Berguedà → dormir allà**: segunda pregunta usa `search_establishments` con destino Berguedà (o equivalente)
- [ ] Escenario **Vall d'Aran → rutes fàcils**: segunda pregunta usa `search_routes` referenciando Vall d'Aran
- [ ] Escenario **idioma**: turno 2 mantiene idioma del turno 1 (ca/es)
- [ ] Escenario **reset**: tras `POST /api/session/reset`, turno siguiente no hereda destino anterior
- [ ] HTTP 200 + SSE `done` en cada turno; ≥80% escenarios PASS
- [ ] Documentar casos en el script (tabla id / mensajes / criterio)

## Capas / archivos principales

- `scripts/uat_context_battery.py` (nuevo)
- `scripts/uat_context_battery_results.txt` (salida)
- `app/services/agent_service.py` (solo si falla y requiere fix)
- `app/prompts/femturisme.py` (refuerzo instrucciones contexto, si hace falta)
- `tests/api/test_chat.py` (opcional: test multi-turn con mismo session_id)

## Issues relacionadas

- `ca-matrix-verification.md`
- `rate-limiting-logging.md`

## Verificación

```powershell
powershell -File scripts/restart-server.ps1
python scripts/uat_context_battery.py
# Umbral: >=80% PASS (p.ej. 4/5 escenarios)
```

## Referencias

- [requeriments.md](../client/requeriments.md) C5, RF-06, CA-07
- [funcional.md](../client/funcional.md) §9
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-605 (CA-07)
