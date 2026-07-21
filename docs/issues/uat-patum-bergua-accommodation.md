## Objetivo

Script UAT end-to-end que reprodueix la conversa Patum → allotjament a prop Berga i valida routing, paràmetres de tool i presentació mínima de resultats.

## Contexto

Golden case manual reportat per l'equip. Complementa UAT recall ([#40](https://github.com/3urega/femturisme/issues/40)) i UAT radi experiències ([#44](https://github.com/3urega/femturisme/issues/44)).

Dependències: #45 (prompt type), #46 (`distance_km`), #47 (≥3 opcions), #48 (seguiments).

## Alcance

| In | Fuera |
|----|-------|
| `scripts/uat_patum_bergua_accommodation.py` amb casos multi-turn | Canvis al repository (issues prèvies) |
| Documentació a [`docs/devs/testing.md`](../devs/testing.md) | Widget PHP |
| Umbral 100% PASS sobre casos definits | Tests LLM no deterministes sense skip documentat |

## Criterios de aceptación

- [ ] **UAT-EST-B01:** «Què en saps de la Patum?» → crides articles/events (recall temàtic OK).
- [ ] **UAT-EST-B02:** «buscam allotjament a prop» → pregunta km o proposa radi; no `type=cases-rurals` sense demanar-ho.
- [ ] **UAT-EST-B03:** confirmació («si» / radi acordat) → `search_establishments` amb `distance_km` quan #46 estigui fet; sense articles/events.
- [ ] **UAT-EST-B04:** «2 o 3 més» → `search_establishments` sense `type` rural; no articles/events; si `total>=3`, resposta menciona ≥3 enllaços o el script valida tool totals.
- [ ] Script escriu `scripts/uat_patum_bergua_accommodation_results.txt`; documentat a `testing.md`.

## Capas / archivos principales

- [`scripts/uat_patum_bergua_accommodation.py`](../../scripts/uat_patum_bergua_accommodation.py)
- [`docs/devs/testing.md`](../devs/testing.md)

## Issues relacionadas

- #45, #46, #47, #48

## Referencias

- [plan-establishments-proximity.md](../devs/plan-establishments-proximity.md)
- [`scripts/uat_experiences_radius.py`](../../scripts/uat_experiences_radius.py) (patró)

## Verificación

```bash
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```
