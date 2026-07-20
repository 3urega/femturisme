# Pla: Recall de catàleg — paritat amb el cercador web (ex. Patum)

**Motiu:** consultes com «Patum», «Què és la Patum?» o «Quan és la Patum?» poden retornar **0 resultats** a l'agent mentre el cercador de femturisme.cat en troba molts ([cercador?q=patum](https://femturisme.cat/cercador?q=patum)).

**Objectiu:** que l'agent trobi el mateix contingut rellevant que el visitant esperaria del cercador, dins l'arquitectura **6 tools MySQL** (sense text-to-SQL ni scraping).

**Estat:** **en curs** — [#36](https://github.com/3urega/femturisme/issues/36)–[#37](https://github.com/3urega/femturisme/issues/37) tancats *(2026-07-20)*; obertes [#38](https://github.com/3urega/femturisme/issues/38)–[#40](https://github.com/3urega/femturisme/issues/40).

---

## Diagnosi (causes arrel)

| # | Problema | Evidència |
|---|----------|-----------|
| 1 | **Cercador web ≠ 6 buscadors** | El cercador del portal fa cerca global full-text; l'agent demana al LLM que triï una tool amb paràmetres estructurats. |
| 2 | **`search_events` sense `query`** | `EventsRepository` filtra només per `destination` + dates; no per `ac.titol` / `descripcio`. «Patum» sense «Berga» no es pot trobar a l'agenda. |
| 3 | **Dates per defecte massa estretes** | `search_events` omple el mes actual si no hi ha dates → esdeveniments com la Patum (juny) es perden fora de finestra. |
| 4 | **Routing LLM insuficient** | Preguntes informatives («Què és…») no forcem cap tool; el model pot respondre sense consultar `search_articles` (`topic`/`query`). |
| 5 | **UAT no cobreix recall temàtic** | `uat_catalog_battery.py` comprova routing de tool, sovint amb `min_total: 0` — no detecta «0 resultats inacceptable». |

**Nota:** `search_articles` **ja té** `query`/`topic` — el gap principal és agenda + orquestració.

---

## Gap vs cercador web

```text
Cercador web:  q=patum  →  tots els tipus (notícies, agenda, pobles, rutes…)

Agent avui:    LLM → 1 tool
               search_events(destination?)  →  sense keyword
               search_articles(query?)      →  només si el LLM ho crida
```

**Objectiu v1:** per consultes amb **termes cercables** (festa, patrimoni, activitat, lloc…), l'agent ha de consultar com a mínim **articles + agenda per keyword** abans de dir «no ho sé». Patum va ser el cas reportat; la solució és **genèrica**, no whitelist de festivals.

---

## Principi d'implementació (no overfitting)

| Correcte | Incorrecte |
|----------|------------|
| `query_keywords.py`: extreure tokens del missatge usuari | `if "patum" in message` o llista tancada de festes |
| Fan-out multi-tool quan hi ha keyword significatiu | Només arreglar el cas Patum als tests |
| Patum com a **golden case** UAT (#40) | Patum com a única lògica de negoci |
| Fallback reactiu (#38) per qualsevol `total=0` | Prompt amb 10 exemples només de Patum |

---

## GitHub issues (draft)

| Ordre | Slug | Títol | GitHub |
|-------|------|-------|--------|
| 1 | ~~`events-keyword-query.md`~~ | Catàleg: search_events amb query i dates intel·ligents | [#36](https://github.com/3urega/femturisme/issues/36) **implementat** *(2026-07-20)* |
| 2 | ~~`agent-theme-routing.md`~~ | Agent: routing per keyword multi-tool (genèric) | [#37](https://github.com/3urega/femturisme/issues/37) **implementat** *(2026-07-20)* |
| 3 | `agent-zero-results-fallback.md` | Agent: fallback keyword quan total=0 | [#38](https://github.com/3urega/femturisme/issues/38) |
| 4 | `prompt-theme-queries.md` | Prompt: guia consultes temàtiques i festivals | [#39](https://github.com/3urega/femturisme/issues/39) |
| 5 | `uat-catalog-recall-battery.md` | UAT recall: golden queries diverses ≥80% | [#40](https://github.com/3urega/femturisme/issues/40) |

Manifest: [manifest.catalog-recall.json](../issues/manifest.catalog-recall.json)

---

## Fora d'abast

- Replicar el cercador Google Site Search al Python (índex global únic).
- Text-to-SQL o LIKE lliure generat per LLM.
- RAG / guies PDF per «Què és la Patum?» (Fase 2; Fase 1 = catàleg MySQL).
- Canvis al CMS PHP del client.

---

## Verificació global (post-batch)

```powershell
python -m pytest tests/integration/sql/test_events.py tests/integration/sql/test_articles.py -v -m integration
python scripts/uat_recall_battery.py http://127.0.0.1:5010
# Manual: «Patum», «Quan és la Patum?», «Articles sobre la Patum de Berga»
# Comparar amb https://femturisme.cat/cercador?q=patum
```

---

## Referències

- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.3 agenda, §4.2 articles
- [sql-mapeo.md](../sql-mapeo.md) §2, §5
- [funcional.md](../client/funcional.md) — exemple «Quan és la Patum?»
- [uat_catalog_battery.py](../../scripts/uat_catalog_battery.py)

**Última actualització:** 2026-07-20 *(clarificació solució genèrica, no whitelist Patum)*
