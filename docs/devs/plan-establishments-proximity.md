# Pla: Allotjament per proximitat i seguiments conversacionals

**Motiu:** conversa reportada (Patum → Berga → «allotjament a prop») amb deficiències:

1. Només 1 opció quan n'hi hauria d'haver diverses al catàleg.
2. Promesa de radi (30 km) sense `distance_km` a `search_establishments`.
3. Seguiment «2 o 3 més» filtra `cases-rurals` sense que l'usuari ho demani.
4. Seguiments d'allotjament tornen a cridar `search_articles` / `search_events` (contaminació del flux temàtic Patum).

**Objectiu:** paritat de comportament amb el portal i respostes útils en diàleg multi-turn.

**Estat:** **completat** — [#45](https://github.com/3urega/femturisme/issues/45)–[#49](https://github.com/3urega/femturisme/issues/49) **tancats** *(2026-07-21)*.

---

## Gap vs conversa real

```text
Usuari: «buscam allotjament a prop» (després de Patum/Berga)
Agent: proposa 30 km → crida search_establishments(destination=Berga) sense radi
       → 1 hotel mostrat; seguiment «2 o 3 més» → type=cases-rurals + articles/events
```

| # | Gap | Estat |
|---|-----|-------|
| 1 | Només 1 opció mostrada | **Resolt** — #47 (prompt CA-05/CA-06) |
| 2 | Radi 30 km sense `distance_km` | **Resolt** — #46 (repository + tool) + prompt #49 |
| 3 | Seguiment filtra `cases-rurals` | **Resolt** — #45 (prompt) |
| 4 | Seguiments criden articles/events | **Resolt** — #48 (query_keywords + prompt) |

**UAT:** [`scripts/uat_patum_bergua_accommodation.py`](../../scripts/uat_patum_bergua_accommodation.py) — validació end-to-end (#49). Veure [testing.md](testing.md).

---

## GitHub issues

| Ordre | Títol | GitHub | Estat |
|-------|-------|--------|-------|
| 1 | Prompt: allotjament genèric sense cases-rurals per defecte | [#45](https://github.com/3urega/femturisme/issues/45) | **Tancat** *(2026-07-21)* |
| 2 | Catàleg: search_establishments amb distance_km | [#46](https://github.com/3urega/femturisme/issues/46) | **Tancat** *(2026-07-21)* |
| 3 | Prompt: llistar mínim 3 opcions quan total>=3 | [#47](https://github.com/3urega/femturisme/issues/47) | **Tancat** *(2026-07-21)* |
| 4 | Agent: seguiments d'allotjament sense flux temàtic | [#48](https://github.com/3urega/femturisme/issues/48) | **Tancat** *(2026-07-21)* |
| 5 | UAT: Patum + allotjament a prop Berga | [#49](https://github.com/3urega/femturisme/issues/49) | **Tancat** *(2026-07-21)* |

---

## Verificació global

```powershell
python -m pytest tests/unit/test_prompts.py tests/integration/sql/test_establishments.py -q
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```

**Última actualització:** 2026-07-21
