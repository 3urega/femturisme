## Objetivo

Tancar la deute de routing revalidant **UAT-EST-B01…B04** al 100% (`scripts/uat_patum_bergua_accommodation.py`) i actualitzant la matriu CA / documentació de testing amb evidència post-fix.

## Contexto

- Script UAT creat a [#49](https://github.com/3urega/femturisme/issues/49); última execució **2/4 PASS** (B03–B04 KO).
- Depèn de prompt (#1) i/o instruccions per torn (#2) per arribar a 4/4 amb LLM real.
- [ca-matrix-fase1.md](../devs/ca-matrix-fase1.md) data 2026-07-14 — cal afegir evidència conversa Patum+Berga.

## Alcance

| In | Fuera |
|----|-------|
| Executar i arribar a **4/4 PASS** UAT-EST-BERG (reinici Flask obligatori) | Canvis repository MySQL |
| Actualitzar `uat_patum_bergua_accommodation_results.txt` com a evidència | Widget PHP (Fase 4) |
| Actualitzar [ca-matrix-fase1.md](../devs/ca-matrix-fase1.md) — nota UAT #49 + data | Sign-off client formal (DEV-606) |
| Actualitzar [testing.md](../devs/testing.md) si cal matisar requisits LLM | Noves features fora del golden case |

## Criterios de aceptación

- [ ] `python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010` → **4/4 PASS** (100%).
- [ ] B03: `search_establishments` amb `distance_km=30`, destination Berga; **cap** `search_experiences`.
- [ ] B04: només `search_establishments`; **cap** articles/events; `total >= 3` si MySQL en té.
- [ ] `ca-matrix-fase1.md` inclou fila o nota UAT Patum+Berga amb data i enllaç a results.txt.
- [ ] [plan-establishments-routing-debt.md](../devs/plan-establishments-routing-debt.md) marcat **completat**.

## Capas / archivos principales

- [`scripts/uat_patum_bergua_accommodation.py`](../../scripts/uat_patum_bergua_accommodation.py)
- [`docs/devs/ca-matrix-fase1.md`](../devs/ca-matrix-fase1.md)
- [`docs/devs/testing.md`](../devs/testing.md)

## Issues relacionadas

- `prompt-proximity-establishments-vs-experiences`
- `agent-accommodation-domain-turn-hints`

## Referencias

- [plan-establishments-routing-debt.md](../devs/plan-establishments-routing-debt.md)
- [requeriments.md](../client/requeriments.md) — CA-05, CA-06, CA-07

## Verificación

```powershell
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```
