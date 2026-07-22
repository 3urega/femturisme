# Pla: Deute routing allotjament vs experiències (proximitat km)

**Motiu:** UAT [#49](https://github.com/3urega/femturisme/issues/49) (`uat_patum_bergua_accommodation.py`) **2/4 PASS**. El backend `#46` (`distance_km` a `search_establishments`) és correcte; el fallo és **routing LLM**:

| Check | Estat | Símptoma |
|-------|-------|----------|
| B03 | FAIL | «30 km des de Berga» després d'allotjament → `search_experiences` en lloc de `search_establishments` |
| B04 | FAIL | «2 o 3 més» → encara `search_articles` / `search_events` (LLM + possible fallback) |

**Causa:** el prompt reforça molt el cas **experiències + km** (UAT Calella #44) però no desambigua prou quan el **domini actiu del diàleg** és dormir/menjar. Missatges curts («30 km», «si») no tenen paraules clau d'establiment → el model reutilitza el patró d'experiències.

**Objectiu:** UAT-EST-B03 i B04 **PASS** (4/4) sense canvis al repository MySQL.

**Estat:** **completat** — [#50](https://github.com/3urega/femturisme/issues/50)–[#52](https://github.com/3urega/femturisme/issues/52) implementades; UAT **4/4 PASS** via [#51](https://github.com/3urega/femturisme/issues/51) *(2026-07-21)*.

---

## Resultat final UAT

```text
UAT-EST-B01…B04: 4/4 PASS (100%) — scripts/uat_patum_bergua_accommodation_results.txt
```

| # | Gap | Solució | Estat |
|---|-----|---------|-------|
| 1 | km sol després d'allotjament → experiències | Prompt §C domini conversacional (#50) | Tancat |
| 2 | Historial no guia el torn curt | Instrucció per torn + `build_forced_search_establishments_input` (#52, #51) | Tancat |
| 3 | UAT encara KO | Revalidació 4/4 + ca-matrix (#51) | Tancat |

---

## GitHub issues (batch tancat)

| Ordre | Títol | GitHub | Estat |
|-------|-------|--------|-------|
| 1 | Prompt: proximitat km allotjament vs experiències | [#50](https://github.com/3urega/femturisme/issues/50) | **Implementat** *(2026-07-21)* |
| 2 | Agent: instrucció per torn domini allotjament actiu | [#52](https://github.com/3urega/femturisme/issues/52) | **Implementat** *(2026-07-21)* |
| 3 | UAT: Patum+Berga 4/4 PASS i ca-matrix | [#51](https://github.com/3urega/femturisme/issues/51) | **Implementat** *(2026-07-21)* |

---

## Gap vs UAT #49 (històric)

```text
Turn 2: buscam allotjament a prop de Berga → agent pregunta km (OK)
Turn 3: 30 km des de Berga → search_experiences (KO — hauria search_establishments + distance_km=30)
Turn 4: 2 o 3 més → articles/events + establishments (KO)
```

| # | Gap | Solució proposada |
|---|-----|-------------------|
| 1 | km sol després d'allotjament → experiències | Prompt: domini conversacional + exemples negatius |
| 2 | Historial no guia el torn curt | Agent: instrucció per torn (domini allotjament actiu) |
| 3 | UAT encara KO | Revalidació + actualitzar ca-matrix | Tancat #51 |

---

## Verificació global (regressió)

```powershell
python -m pytest tests/unit/test_prompts.py tests/unit/test_domain_hints.py -q
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```

**Última actualització:** 2026-07-21