## Objetivo

Bateria **UAT** per validar paritat de recall entre agent i portal per **ofertes per radi**: cas golden Calella + 50 km + Visites guiades.

## Contexto

- Referència web: [ofertes/visites-guiades?ubicacio=calella&distancia=50](https://femturisme.cat/ofertes/visites-guiades?ubicacio=calella&distancia=50) (~7 resultats)
- Patró scripts: [`uat_recall_battery.py`](../../scripts/uat_recall_battery.py), [`uat_catalog_battery.py`](../../scripts/uat_catalog_battery.py)
- Prerequisits: issues radi + prompt (#41–#43 del batch, números pendents de publicació)

## Alcance

| In | Fuera |
|----|-------|
| Script `scripts/uat_experiences_radius.py` (1–3 casos) | Scraping HTML portal |
| Cas UAT-EXP-R01: missatge «Visitas guiades a 50 km de Calella» → `total >= 1`, URL femturisme.cat | Comparació automàtica 1:1 amb HTML |
| Skip sense MYSQL_* (exit 0) | CI bloquejant sense staging |

## Criterios de aceptación

- [ ] Script imprimeix tools, `distance_km`, totals i URL primera card
- [ ] UAT-EXP-R01 PASS contra staging amb servidor + LLM real
- [ ] Documentat a [`testing.md`](../devs/testing.md)
- [ ] Opcional: ampliar `uat_catalog_battery.py` cas UAT-EXP-03 amb `min_total: 1` radi

## Capas / archivos principales

- `scripts/uat_experiences_radius.py`
- `docs/devs/testing.md`

## Issues relacionadas

- Prerequisits: `geo-radius-helper.md`, `experiences-distance-km.md`, `prompt-experiences-radius.md`

## Verificación

```powershell
python main.py
python scripts/uat_experiences_radius.py http://127.0.0.1:5010
```

## Referencias

- [plan-experiences-radius.md](../devs/plan-experiences-radius.md)
