## Objetivo

Afegir cerca per **text lliure** a `search_events` (paràmetre `query`) per trobar esdeveniments per nom o tema (p. ex. «Patum», «Fira medieval», «Mercat de nadal») com fa el cercador web a l'agenda, sense dependre només de `destination`.

**Nota:** Patum és cas de prova representatiu; el paràmetre `query` és genèric per a qualsevol terme.

## Contexto

- Avui [`EventsRepository`](../../app/db/repositories/events.py) filtra per territori + interval de dates; **no** per `agenda_continguts.titol`.
- [`search_articles`](../../app/db/repositories/articles.py) ja accepta `query`/`topic`; l'agenda no.
- Consulta usuari típica: «Quan és la Patum?» → cal match a `ac.titol LIKE %patum%`.
- [`sql-mapeo.md` §5](../sql-mapeo.md) documenta només `destination`, `date_from`, `date_to`.

## Alcance

| In | Fuera |
|----|-------|
| Paràmetre opcional `query` a tool + repository | Cerca global multi-taula (un sol índex) |
| SQL: `AND (query IS NULL OR ac.titol LIKE … OR ac.descripcio LIKE …)` | Canvis al CMS MySQL |
| Si hi ha `query` i no dates: finestra per defecte **12 mesos** (no només mes actual) | RAG |
| `destination` opcional quan `query` present (com articles) | Scraping |
| Tests integració SQL + unitat mapper | |

## Criterios de aceptación

- [ ] `events.search(query="patum")` retorna ≥1 resultat contra MySQL staging (si el cercador web també en troba)
- [ ] `events.search(destination="Berga", query="patum")` filtra per ambdós
- [ ] Sense `query`, comportament actual (destination required + mes actual per defecte) es manté
- [ ] Tool SCHEMA documenta `query` i interacció amb dates
- [ ] [`sql-mapeo.md` §5](../sql-mapeo.md) actualitzat
- [ ] Test `tests/integration/sql/test_events.py` amb cas Patum (skip si MYSQL_* absent)

## Capas / archivos principales

- `app/db/repositories/events.py`
- `app/services/tools/events.py`
- `docs/sql-mapeo.md` §5
- `tests/integration/sql/test_events.py`

## Issues relacionadas

- `agent-theme-routing.md`
- `uat-catalog-recall-battery.md`

## Verificación

```powershell
python -m pytest tests/integration/sql/test_events.py -v -m integration
python -c "from app.db.repositories import events; print(events.search(query='patum')['total'])"
```

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md)
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §4.3
