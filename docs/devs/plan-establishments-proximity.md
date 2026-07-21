# Pla: Allotjament per proximitat i seguiments conversacionals

**Motiu:** conversa reportada (Patum → Berga → «allotjament a prop») amb deficiències:

1. Només 1 opció quan n'hi hauria d'haver diverses al catàleg.
2. Promesa de radi (30 km) sense `distance_km` a `search_establishments`.
3. Seguiment «2 o 3 més» filtra `cases-rurals` sense que l'usuari ho demani.
4. Seguiments d'allotjament tornen a cridar `search_articles` / `search_events` (contaminació del flux temàtic Patum).

**Objectiu:** paritat de comportament amb el portal i respostes útils en diàleg multi-turn.

**Estat:** **publicat** — issues [#45](https://github.com/3urega/femturisme/issues/45)–[#49](https://github.com/3urega/femturisme/issues/49) *(2026-07-21)*.

---

## Gap vs conversa real

```text
Usuari: «buscam allotjament a prop» (després de Patum/Berga)
Agent: proposa 30 km → crida search_establishments(destination=Berga) sense radi
       → 1 hotel mostrat; seguiment «2 o 3 més» → type=cases-rurals + articles/events
```

**Backend:** `search_establishments` encara **no** té `distance_km` (només `search_experiences`, batch #41–#44).

---

## GitHub issues (draft)

| Ordre | Títol | Fitxer |
|-------|-------|--------|
| 1 | Prompt: allotjament genèric sense cases-rurals per defecte | [establishments-generic-type-prompt.md](../issues/establishments-generic-type-prompt.md) |
| 2 | Catàleg: search_establishments amb distance_km | [establishments-distance-km.md](../issues/establishments-distance-km.md) |
| 3 | Prompt: llistar mínim 3 opcions quan total>=3 | [prompt-min-three-results.md](../issues/prompt-min-three-results.md) |
| 4 | Agent: seguiments d'allotjament sense flux temàtic | [establishments-followup-routing.md](../issues/establishments-followup-routing.md) |
| 5 | UAT: Patum + allotjament a prop Berga | [uat-patum-bergua-accommodation.md](../issues/uat-patum-bergua-accommodation.md) |

Manifest: [manifest.establishments-proximity.json](../issues/manifest.establishments-proximity.json)

---

## Verificació global

```powershell
python -m pytest tests/unit/test_prompts.py tests/integration/sql/test_establishments.py -q
python main.py
python scripts/uat_patum_bergua_accommodation.py http://127.0.0.1:5010
```

**Última actualització:** 2026-07-21
