## Objetivo

Bateria **UAT de recall** (no només routing): consultes temàtiques diverses han de retornar **`total ≥ 1`** i enllaços femturisme.cat quan el cercador web en troba.

**Patum és un golden case obligatori** (el bug reportat), però la bateria ha de cobrir **≥5 temes diferents** per evitar overfitting.

## Contexto

- [`uat_catalog_battery.py`](../../scripts/uat_catalog_battery.py) (DEV-604) valida `expected_tool` però molts casos tenen `min_total: 0` → no detecta recall zero inacceptable.
- Referència manual del bug original: [femturisme.cat/cercador?q=patum](https://femturisme.cat/cercador?q=patum)
- Golden queries inicials (mínim 5, dominis variats):
  - Patum / Berga (festa, informativa + agenda)
  - Fira medieval Pals (agenda)
  - Castellers Barcelona (articles/tema)
  - Parc Natural del Cadí (articles/destí)
  - Sant Jordi o similar (estacional; documentar skip si fora de temporada)

## Alcance

| In | Fuera |
|----|-------|
| Nou script `scripts/uat_recall_battery.py` | Scraping del cercador Google |
| Casos amb `min_total ≥ 1` contra MySQL staging | CI bloquejant sense MYSQL_* (skip documentat) |
| Informe text + exit code si <80% pass | Comparació automàtica HTML cercador web |
| Cada cas defineix `keywords` esperats, no nom de festival hardcoded al agent | Només casos Patum a la bateria |

## Criterios de aceptación

- [ ] ≥5 casos recall amb `min_total ≥ 1`, **màxim 1 pot ser Patum** com a cas principal; la resta temes diversos
- [ ] Script imprimeix tool(s) cridada(s), total i URLs de la primera card
- [ ] Documentat a [`testing.md`](../devs/testing.md)
- [ ] Umbral ≥80% pass (com DEV-604)
- [ ] Executar després d'implementar #36 + #37

## Capas / archivos principales

- `scripts/uat_recall_battery.py` (nou)
- `docs/devs/testing.md`
- Opcional: ampliar `docs/devs/ca-matrix-fase1.md`

## Issues relacionadas

- [#36](https://github.com/3urega/femturisme/issues/36) events-keyword-query
- [#37](https://github.com/3urega/femturisme/issues/37) agent-theme-routing
- [#38](https://github.com/3urega/femturisme/issues/38) agent-zero-results-fallback

## Verificación

```powershell
python scripts/uat_recall_battery.py http://127.0.0.1:5010
# Esperat post-fix: UAT-REC-01 Patum PASS + ≥4 casos addicionals PASS
```

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md)
- [tecnic.md](../client/tecnic.md) §14.3
