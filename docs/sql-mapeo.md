# sql-mapeo.md — Queries MySQL per buscadors de catàleg (v1.1)

Document de **Fase 2**. Omplir abans d'implementar repositoris a Fase 3.

**Domini:** [dominio-femturisme-ca.md](dominio-femturisme-ca.md)  
**Estat:** ☐ esborrany · ☐ revisat · ☐ tancat

---

## Resum

| # | Tool | Repository | Taules principals | SQL provada | Casos prova |
|---|------|------------|-------------------|-------------|-------------|
| 1 | `search_establishments` | `EstablishmentsRepository` | _TBD (establiments)_ | ☐ | ☐ |
| 2 | `search_articles` | `ArticlesRepository` | _TBD_ | ☐ | ☐ |
| 3 | `search_destinations` | `DestinationsRepository` | _TBD (poblacions)_ | ☐ | ☐ |
| 4 | `search_routes` | `RoutesRepository` | _TBD_ | ☐ | ☐ |
| 5 | `search_events` | `EventsRepository` | _TBD (agenda)_ | ☐ | ☐ |
| 6 | `search_experiences` | `ExperiencesRepository` | _TBD_ | ☐ | ☐ |

**Nota migració:** el prototip antic usava `search_accommodations` i `search_experiences` (ofertes). Veure [dominio-femturisme-ca.md](dominio-femturisme-ca.md) §6.

---

## Format JSON comú (sortida)

Veure [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) §5.7 — card + wrapper amb `results[]`, camps `title`, `url`, `image`, `description`, `date` (si escau).

---

## 1. search_establishments

**Domini:** on dormir i on menjar (mateixa taula, filtre per tipus)  
**Fitxer tool (objectiu):** `app/services/tools/establishments.py`  
**Paràmetres:** `destination` (required), `type` (optional)

### 1.1 Taules i relacions

_TODO — confirmar amb `docs/schema.sql`_

### 1.2 Query SQL final

```sql
-- TODO: establiments + tipus + ubicació
-- LIMIT 20
```

### 1.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `title` | |
| | `url` | prefix TBD: `/on-dormir/` o `/on-menjar/` |
| | `type` | tipus establiment |

### 1.4 Casos de prova

| # | destination | type | Files min | URL provada |
|---|-------------|------|-----------|-------------|
| 1 | Girona | hotel | ≥ 0 | ☐ |
| 2 | Pals | restaurant | ≥ 0 | ☐ |

---

## 2. search_articles

**Domini:** articles / notícies  
**Fitxer tool:** `app/services/tools/articles.py`  
**Paràmetres:** `destination?`, `topic?`, `query?`

### 2.1 Taules i relacions

_TODO_

### 2.2 Query SQL final

```sql
-- TODO
```

### 2.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `title` | |
| | `url` | TBD |
| | `description` | resum |

### 2.4 Casos de prova

| # | topic / query | Files min | URL provada |
|---|---------------|-----------|-------------|
| 1 | Parc Natural Cadí | ≥ 0 | ☐ |

---

## 3. search_destinations

**Domini:** on anar — pobles i llocs  
**Fitxer tool:** `app/services/tools/destinations.py`  
**Paràmetres:** `destination` (required), `region?`

### 3.1 Taules i relacions

_TODO_

### 3.2 Query SQL final

```sql
-- TODO
```

### 3.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `title` | nom població/lloc |
| | `description` | text descriptiu |
| | `url` | TBD |

### 3.4 Casos de prova

| # | destination | Files min | URL provada |
|---|-------------|-----------|-------------|
| 1 | Besalú | ≥ 0 | ☐ |
| 2 | Empordà | ≥ 0 | ☐ |

---

## 4. search_routes

**Domini:** rutes  
**Fitxer tool:** `app/services/tools/routes_tool.py`  
**URL web referència:** `https://www.femturisme.cat/rutes?ubicacio={destination}`  
**Paràmetres:** `destination` (required), `type?`

### 4.1 Taules i relacions

_TODO_

### 4.2 Query SQL final

```sql
-- TODO
```

### 4.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `url` | `https://www.femturisme.cat/rutes/` + slug |

### 4.4 Casos de prova

| # | destination | type | Files min | URL provada |
|---|-------------|------|-----------|-------------|
| 1 | Pirineu | A peu | ≥ 0 | ☐ |
| 2 | Empordà | En bicicleta | ≥ 0 | ☐ |

---

## 5. search_events

**Domini:** agenda — esdeveniments de calendari  
**Fitxer tool:** `app/services/tools/events.py`  
**URL web referència:** `https://www.femturisme.cat/agenda?ubicacio={destination}`  
**Paràmetres:** `destination` (required), `date_from?`, `date_to?`

### 5.1 Taules i relacions

_TODO_

### 5.2 Query SQL final

```sql
-- TODO: filtrar per interval dates si date_from/date_to informats
-- Només esdeveniments vigents/futurs
```

### 5.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `date` | data o rang |
| | `url` | `/agenda/` + slug |

### 5.4 Casos de prova

| # | destination | date_from | date_to | Files min | URL provada |
|---|-------------|-----------|---------|-----------|-------------|
| 1 | Empordà | cap setmana | cap setmana | ≥ 0 | ☐ |
| 2 | Barcelona | 2026-06-01 | 2026-06-30 | ≥ 0 | ☐ |

---

## 6. search_experiences

**Domini:** experiències promocionals (establiment o població) — **no** confondre amb agenda  
**Fitxer tool:** `app/services/tools/experiences.py`  
**Paràmetres:** `destination` (required), `category?`, `establishment?`

### 6.1 Taules i relacions

_TODO — relació amb establiments/poblacions_

### 6.2 Query SQL final

```sql
-- TODO
```

### 6.3 Mapatge columna → JSON

| Columna SQL | Camp JSON | Notes |
|-------------|-----------|-------|
| | `title` | |
| | `url` | TBD |
| | `location` | municipi / establiment |

### 6.4 Casos de prova

| # | destination | category / establishment | Files min | URL provada |
|---|-------------|--------------------------|-----------|-------------|
| 1 | Olvan | arrossada | ≥ 0 | ☐ |
| 2 | Berguedà | Sant Valentí | ≥ 0 | ☐ |

---

## Tancament Fase 2

- [ ] 6 tools amb query documentada i provada a MySQL staging
- [ ] SCHEMA de tools revisit (6 operacions + guies PDF)
- [ ] Preguntes obertes de [dominio-femturisme-ca.md](dominio-femturisme-ca.md) §7 resoltes o documentades
