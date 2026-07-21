# Pla: Deute routing allotjament vs experiències (proximitat km)

**Motiu:** UAT [#49](https://github.com/3urega/femturisme/issues/49) (`uat_patum_bergua_accommodation.py`) **2/4 PASS**. El backend `#46` (`distance_km` a `search_establishments`) és correcte; el fallo és **routing LLM**:

| Check | Estat | Símptoma |
|-------|-------|----------|
| B03 | FAIL | «30 km des de Berga» després d'allotjament → `search_experiences` en lloc de `search_establishments` |
| B04 | FAIL | «2 o 3 més» → encara `search_articles` / `search_events` (LLM + possible fallback) |

**Causa:** el prompt reforça molt el cas **experiències + km** (UAT Calella #44) però no desambigua prou quan el **domini actiu del diàleg** és dormir/menjar. Missatges curts («30 km», «si») no tenen paraules clau d'establiment → el model reutilitza el patró d'experiències.

**Objectiu:** UAT-EST-B03 i B04 **PASS** (4/4) sense canvis al repository MySQL.

**Estat:** **obert** — issues draft pendents de publicar.

---

## Gap vs UAT #49

```text
Turn 2: buscam allotjament a prop de Berga → agent pregunta km (OK)
Turn 3: 30 km des de Berga → search_experiences (KO — hauria search_establishments + distance_km=30)
Turn 4: 2 o 3 més → articles/events + establishments (KO)
```

| # | Gap | Solució proposada |
|---|-----|-------------------|
| 1 | km sol després d'allotjament → experiències | Prompt: domini conversacional + exemples negatius |
| 2 | Historial no guia el torn curt | Agent: instrucció per torn (domini allotjament actiu) |
| 3 | UAT encara KO | Revalidació + actualitzar ca-matrix |

---

## GitHub issues (draft)

| Ordre | Slug | Títol | Depèn de |
|-------|------|-------|----------|
| 1 | `prompt-proximity-establishments-vs-experiences` | Prompt: proximitat km allotjament vs experiències | — |
| 2 | `agent-accommodation-domain-turn-hints` | Agent: instrucció per torn quan domini allotjament actiu | #1 (recomanat) |
| 3 | `uat-establishments-proximity-regression` | UAT: Patum+Berga 4/4 PASS i actualitzar ca-matrix | #1, #2 |

Manifest: [manifest.establishments-routing-debt.json](../issues/manifest.establishments-routing-debt.json)

---

## Verificació global

```powershell
python -m pytest tests/unit/test_prompts.py tests/unit/test_domain_hints.py -q
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```

**Última actualització:** 2026-07-21
