# Pla: Experiències per radi geogràfic (paritat `/ofertes?distancia=`)

**Motiu:** el portal permet cerques com [visites guiades a 50 km de Calella](https://femturisme.cat/ofertes/visites-guiades?ubicacio=calella&distancia=50) (`ubicacio` + `distancia` + `tipus`). L'agent avui només filtra per **poble/comarca LIKE** via `search_experiences(destination)` — no per radi km.

**Objectiu:** afegir paràmetre opcional `distance_km` a `search_experiences` per retornar ofertes dins d'un radi des d'un punt d'origen resolt des del catàleg MySQL, mantenint `category` (p. ex. `Visites guiades`).

**Estat:** **draft** — issues locals a `docs/issues/manifest.experiences-radius.json`.

---

## Gap vs portal web

```text
Portal:  /ofertes/visites-guiades?ubicacio=calella&distancia=50
         → ofertes dins 50 km de Calella (Alta Alella, Mogoda, Barcelona…)

Agent:   search_experiences(destination="Calella", category="Visites guiades")
         → només ofertes amb poble/comarca ~ Calella (més estret)
```

**Referència funcional:** domini §4.6 experiències promocionals; `agente.md` mapping `ubicacio` / `tipus` (legacy scraping doc encara útil per contracte URL).

---

## Hipòtesi tècnica (validar a VS1)

| Peça | Font |
|------|------|
| Coordenades origen | `poble_general.latitud/longitud` per municipi; `generic_ubicacions` per zones agregades |
| Coordenades oferta | `establiment_general.latitud/longitud` o `poble_general` de l'oferta |
| Filtre radi | Haversine MySQL (km) quan `distance_km` present |
| Comportament sense coords | Fallback a filtre territorial actual + `meta.hint` |

**Fora d'abast v1:** replicar el filtre a `search_establishments`, `search_events`, etc.; canvis PHP CMS; scraping.

---

## GitHub issues (draft)

| Ordre | Slug | Títol |
|-------|------|-------|
| 1 | `geo-radius-helper.md` | Catàleg: helper radi km i SQL Haversine (territory) |
| 2 | `experiences-distance-km.md` | Catàleg: search_experiences amb distance_km |
| 3 | `prompt-experiences-radius.md` | Prompt: ofertes «a X km de Y» i visites guiades |
| 4 | `uat-experiences-radius.md` | UAT: visites guiades Calella 50 km vs portal |

Manifest: [manifest.experiences-radius.json](../issues/manifest.experiences-radius.json)

---

## Verificació global (post-batch)

```powershell
python -m pytest tests/integration/sql/test_experiences.py -v -m integration
python scripts/uat_experiences_radius.py http://127.0.0.1:5010
# Manual: comparar amb https://femturisme.cat/ofertes/visites-guiades?ubicacio=calella&distancia=50
```

**Última actualització:** 2026-07-20
