# Matriu CA — Fase producte 1 (chat Flask demo)

**Issue:** [#25](https://github.com/3urega/femturisme/issues/25) · **Checklist:** DEV-605  
**Entorn:** `http://127.0.0.1:5010/` (demo Flask; staging PHP posposat — Fase 4)  
**Última execució UAT:** 2026-07-21 (UAT-EST-BERG 4/4; abans 2026-07-14)  
**Resum:** **9/9 CA OK** (evidència pre-staging)

Font criteris: [requeriments.md](../client/requeriments.md) §12.

---

## Resum executiu

| Àrea | Resultat |
|------|----------|
| UAT catàleg (DEV-604) | 12/12 PASS, routing 100% |
| UAT idiomes (DEV-601) | 7/8 PASS (88%) — no bloqueja CA individuals |
| UAT context CA-07 (#24) | 5/5 PASS (100%) |
| UAT Patum+Berga (#49/#51) | 4/4 PASS (100%) |
| CA-04 multi-font | PASS — 2 tools (`establishments` + `events`) |
| pytest (API + tools + prompts + domain_hints) | 35+ unit |

---

## Matriu CA-01…CA-09

| CA | Descripció | Estat | Evidència | Reproducció | Nota |
|----|------------|-------|-----------|-------------|------|
| **CA-01** | Interacció en llenguatge natural | **OK** | Chat Flask + widget [`app/static/js/chat.js`](../../app/static/js/chat.js); `tests/api/test_chat.py::test_api_02` | `python -m pytest tests/api/test_chat.py::test_api_02 -v` | Visitant escriu text lliure; resposta SSE amb `text_chunk` + `done` |
| **CA-02** | Interpretació de la intenció (consultes habituals) | **OK** | [`scripts/uat_catalog_battery_results.txt`](../../scripts/uat_catalog_battery_results.txt) — 12/12 routing | `python scripts/uat_catalog_battery.py` | 2 proves per domini; tool esperada en cada cas |
| **CA-03** | Fonts consultades sense exposar funcionament intern | **OK** | UI mostra «cercant…» en `tool_call`; usuari rep text final sense SQL/schemas | Prova manual: obrir `http://127.0.0.1:5010/`, preguntar «Rutes a peu a l'Empordà» | Indicador de càrrega acceptable; no es mostra SQL ni noms de repositories |
| **CA-04** | Combinar diverses fonts quan cal | **OK** | [`scripts/uat_ca04_multi_source_results.txt`](../../scripts/uat_ca04_multi_source_results.txt) | `python scripts/uat_ca04_multi_source.py` | Pregunta composta Girona → `search_establishments` + `search_events` en un torn |
| **CA-05** | Enllaços a femturisme.cat | **OK** | UAT catàleg: `links_ok=True` en casos amb `total>0` (EST, DST, RTE, EVT, EXP-01, ART-02) | Veure `uat_catalog_battery_results.txt` | Casos `total=0` poden no tenir enllaços (comportament esperat) |
| **CA-06** | Alternatives quan no hi ha coincidències exactes | **OK** | UAT EXP-02 (`total=0`); prompt `meta.hint` a [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py); resposta demana precisar zona | `python scripts/uat_catalog_battery.py` (UAT-EXP-02) | Agent proposa aclariment en lloc de canviar de domini |
| **CA-07** | Mantenir context conversacional | **OK** | [`scripts/uat_context_battery_results.txt`](../../scripts/uat_context_battery_results.txt) — 5/5 PASS; [`scripts/uat_patum_bergua_accommodation_results.txt`](../../scripts/uat_patum_bergua_accommodation_results.txt) — UAT-EST-BERG 4/4 *(2026-07-21)* | `python scripts/uat_context_battery.py`; `python scripts/uat_patum_bergua_accommodation.py` | Berguedà→dormir; Patum→allotjament Berga→km→seguiment (#49–#51) |
| **CA-08** | No inventar informació | **OK** | Prompt §CA-08; UAT-ART-01 i UAT-EXP-02 amb `total=0` i `links=False`; resposta honesta sense URLs inventades | Revisar sortida UAT-ART-01/EXP-02 al xat | Regles `meta` + només enllaços de `results[]` |
| **CA-09** | Noves fonts sense canviar model funcional | **OK** | 6 tools MySQL a `CATALOG_TOOLS`; `tests/unit/test_tools_registry.py`; [`docs/text-to-sql-desventajas.md`](../text-to-sql-desventajas.md); [`docs/arquitectura/`](../arquitectura/index.md) | `python -m pytest tests/unit/test_tools_registry.py -v` | Afegir buscador = nou repository + tool + registre; sense text-to-SQL al xat |

---

## Scripts i resultats enllaçats

| Script | Resultat | DEV / issue |
|--------|----------|-------------|
| [`scripts/uat_catalog_battery.py`](../../scripts/uat_catalog_battery.py) | [`uat_catalog_battery_results.txt`](../../scripts/uat_catalog_battery_results.txt) | DEV-604 |
| [`scripts/uat_recall_battery.py`](../../scripts/uat_recall_battery.py) | [`uat_recall_battery_results.txt`](../../scripts/uat_recall_battery_results.txt) | #40 recall temàtic |
| [`scripts/uat_languages_battery.py`](../../scripts/uat_languages_battery.py) | [`uat_languages_battery_results.txt`](../../scripts/uat_languages_battery_results.txt) | DEV-601 |
| [`scripts/uat_context_battery.py`](../../scripts/uat_context_battery.py) | [`uat_context_battery_results.txt`](../../scripts/uat_context_battery_results.txt) | #24 / CA-07 |
| [`scripts/uat_ca04_multi_source.py`](../../scripts/uat_ca04_multi_source.py) | [`uat_ca04_multi_source_results.txt`](../../scripts/uat_ca04_multi_source_results.txt) | CA-04 |
| [`scripts/uat_patum_bergua_accommodation.py`](../../scripts/uat_patum_bergua_accommodation.py) | [`uat_patum_bergua_accommodation_results.txt`](../../scripts/uat_patum_bergua_accommodation_results.txt) | #49 / #51 / CA-07 |

---

## Comandes de verificació completa

```powershell
powershell -File scripts/restart-server.ps1
python scripts/uat_catalog_battery.py
python scripts/uat_recall_battery.py
python scripts/uat_languages_battery.py
python scripts/uat_context_battery.py
python scripts/uat_ca04_multi_source.py
python scripts/uat_patum_bergua_accommodation.py
python -m pytest tests/api/ tests/unit/test_tools_registry.py tests/unit/test_prompts.py tests/unit/test_domain_hints.py -q
```

---

## Limits coneguts (pre-staging)

- Evidència al **chat Flask demo**, no al portal PHP (Fase 4 posposada).
- DEV-606 (sign-off client staging) i DEV-607 (producció) queden oberts.
- UAT idiomes: 1 cas ES amb resposta mixta (UAT-LANG-ES-01); no afecta cap CA individual.

---

## Historial

| Data | Canvi |
|------|-------|
| 2026-07-21 | UAT-EST-BERG 4/4 PASS (#51); evidència Patum→allotjament Berga; forced establishments server-side |
| 2026-07-14 | Matriu inicial DEV-605; 9/9 CA OK; issue #25 |
