# Pla: Experiències per radi geogràfic (paritat `/ofertes?distancia=`)

**Motiu:** el portal permet cerques com [visites guiades a 50 km de Calella](https://femturisme.cat/ofertes/visites-guiades?ubicacio=calella&distancia=50) (`ubicacio` + `distancia` + `tipus`).

**Objectiu:** paràmetre opcional `distance_km` a `search_experiences`, prompt conversacional de proximitat i UAT end-to-end.

**Estat:** **completat** — issues [#41](https://github.com/3urega/femturisme/issues/41)–[#44](https://github.com/3urega/femturisme/issues/44) implementades *(2026-07-21)*.

---

## Gap vs portal web (resolt a nivell backend)

```text
Portal:  /ofertes/visites-guiades?ubicacio=calella&distancia=50
         → ofertes dins 50 km de Calella

Agent:   search_experiences(destination=Calella, category=Visites guiades, distance_km=50)
         → radi Haversine + meta.scope=radius (quan el LLM passa distance_km)
```

**Pendent producte:** ~~el UAT manual (`uat_experiences_radius.py`) pot fallar si el LLM no passa `distance_km`~~ **Resolt** amb iteració de prompt (Opció A) *(2026-07-21)* — cal **reiniciar** el servidor Flask després de canvis al prompt.

### UAT post-iteració prompt

```text
python scripts/uat_experiences_radius.py http://127.0.0.1:5011
→ 2/2 PASS (UAT-EXP-R01 + UAT-EXP-R02)
  distance_km=50, meta.scope=radius, total=6, URL /ofertes/...
```

Canvis aplicats: [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py) (rama A OBLIGATORI abans del diàleg), guia `search_experiences`, bullet «Com treballar», `meta.scope=radius`; [`app/services/tools/experiences.py`](../../app/services/tools/experiences.py) (SCHEMA `distance_km`).

---

## GitHub issues

| Ordre | Títol | GitHub |
|-------|-------|--------|
| 1 | Helper radi km i SQL Haversine | [#41](https://github.com/3urega/femturisme/issues/41) |
| 2 | search_experiences amb distance_km | [#42](https://github.com/3urega/femturisme/issues/42) |
| 3 | Prompt proximitat (preguntar km) | [#43](https://github.com/3urega/femturisme/issues/43) |
| 4 | UAT Calella 50 km vs portal | [#44](https://github.com/3urega/femturisme/issues/44) |

---

## Verificació global

```powershell
python -m pytest tests/integration/sql/test_experiences.py -v -m integration -k calella
python main.py
python scripts/uat_experiences_radius.py http://127.0.0.1:5010
# Manual: comparar amb https://femturisme.cat/ofertes/visites-guiades?ubicacio=calella&distancia=50
```

**Última actualització:** 2026-07-21 (batch #41–#44 tancat; UAT LLM 2/2 PASS després d'iteració prompt)
