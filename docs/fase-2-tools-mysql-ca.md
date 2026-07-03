# Fase 2 — Exploració MySQL i disseny de queries

> **v1.1:** objectiu **6 buscadors** de catàleg. Veure [dominio-femturisme-ca.md](dominio-femturisme-ca.md) i [sql-mapeo.md](sql-mapeo.md). El cos d'aquest document encara descriu el prototip de 4 tools — usar el domini com a referència.

**Guia per al developer.** Respon preguntes bàsiques i explica què fer abans de programar la Fase 3.

**Prerequisits:** Fase 0 (MySQL read-only + `docs/schema.sql`) i Fase 1 (agent Python amb connexió a MySQL).

**Lliurable d'aquesta fase:** fitxer **`docs/sql-mapeo.md`** complet (**6 tools**). La Fase 3 copia la SQL d'aquí al codi Python.

---

## Preguntes ràpides (respostes directes)

### Quantes tools crearem?

**Cap de nova.** Ja en tenim **4 de catàleg** al codi:

| # | Tool | Fitxer |
|---|------|--------|
| 1 | `search_experiences` | `app/services/tools/experiences.py` |
| 2 | `search_accommodations` | `app/services/tools/accommodations.py` |
| 3 | `search_events` | `app/services/tools/events.py` |
| 4 | `search_routes` | `app/services/tools/routes_tool.py` |

Registrades a `app/services/tools/__init__.py` → `ALL_TOOLS`.

La Fase 2 **no afegeix tools**. Dissenya la SQL per a aquestes 4.

*(Més endavant, Fases 5–6, afegirem `search_municipality_guides` per PDFs — això és altra fase, altra BD.)*

### Cada tool serà una query?

**Sí: una query principal `SELECT` per tool** (parametritzada amb placeholders).

| Tool | Queries típiques |
|------|------------------|
| Cada una de les 4 | **1× SELECT** que retorna les files (màx. 20) |
| Opcional | **1× COUNT** si cal `total` exacte i el SELECT és pesat — moltes vegades n'hi ha prou amb `LIMIT 20` + `len(results)` a v1 |

**No** cal una query per cada pregunta d'usuari. El LLM tradueix *«activitats familiars al Berguedà»* → `search_experiences(destination="Berguedà", category="Familiar")` → **la mateixa SQL** amb paràmetres diferents.

### Qui escriu la SQL?

| Qui | Què escriu |
|-----|------------|
| **Developer (Fase 2)** | SQL fixa + documentació a `sql-mapeo.md` |
| **LLM** | **No** escriu SQL. Només tria tool + paràmetres (`destination`, `category`…) |
| **Python (Fase 3)** | Copia la SQL al repositori i l'executa amb `%s` |

### Què és `sql-mapeo.md`?

Document **per a programadors** (no el llegeix el LLM). Per cada tool conté:

- Quines taules i JOINs
- La query SQL final
- Mapatge columna → camp JSON
- Regles de negoci (`publicat = 1`, etc.)
- 3–5 casos de prova amb resultat esperat

Plantilla buida: [`docs/sql-mapeo.md`](./sql-mapeo.md).

### Fase 2 vs Fase 3 — quina diferència?

| | Fase 2 | Fase 3 |
|---|--------|--------|
| **On treballes** | DBeaver + `sql-mapeo.md` | Codi Python (`app/db/repositories/`) |
| **Output** | SQL provada i documentada | Repositoris + tests + `execute()` refactor |
| **Programar agent?** | No | Sí |

### Com relacionem scraping actual amb MySQL?

Avui cada tool fa scraping d'una URL de femturisme.cat. Això és la **pista** per trobar dades a MySQL:

| Tool | URL scrape (avui) | Paràmetres query string | Secció web |
|------|-------------------|-------------------------|------------|
| `search_experiences` | `/ofertes` | `ubicacio`, `tipus` | Ofertes |
| `search_accommodations` | `/on-dormir` | `ubicacio`, `tipus` | Allotjaments |
| `search_events` | `/agenda` | `ubicacio`, `data_inici`, `data_fi` | Agenda |
| `search_routes` | `/rutes` | `ubicacio`, `tipus` | Rutes |

La Fase 2 ha de respondre: **quines taules MySQL alimenten aquesta llista** i com es filtren `ubicacio` / `tipus` / dates.

---

## 1. Què has de fer (una frase)

Per **cadascuna de les 4 tools**, descobrir quines taules MySQL usa femturisme, escriure **una SQL parametritzada**, provar-la a staging i documentar-ho tot a **`docs/sql-mapeo.md`**.

---

## 2. Flux de treball

```
docs/schema.sql          DBeaver / Workbench        docs/sql-mapeo.md
(estructura offline)  →  provar SELECTs        →  SQL final + casos prova
        ↑                        ↑
   Fase 0                  MySQL staging (agent_read)
```

Per **cada tool**, repeteix:

```
A. Identificar taules (schema + comparar amb web/scrape)
B. Escriure SELECT amb placeholders
C. Executar 3–5 casos reals a MySQL
D. Verificar URLs i camps JSON (comparar amb scraping)
E. Omplir secció a sql-mapeo.md
```

**Ordre recomanat:** `search_experiences` → `search_accommodations` → `search_events` → `search_routes` (la primera serveix de plantilla).

---

## 3. Eines que necessites

| Eina | Per a què |
|------|-----------|
| **DBeaver** o **MySQL Workbench** | Executar SQL contra staging |
| **`docs/schema.sql`** | Veure taules sense connectar a prod |
| **Credencials `agent_read`** | Usuari Fase 0, només SELECT |
| **Navegador** | Obrir femturisme.cat/ofertes?ubicacio=Berguedà i comparar resultats |
| **Repo PHP** (opcional) | Si no s'entén un JOIN, mirar com ho fa el CMS |

---

## 4. Pas a pas — exemple `search_experiences`

### 4.1 Obrir el SCHEMA de la tool (ja existeix, no inventar paràmetres nous sense motiu)

```python
# app/services/tools/experiences.py
'properties': {
    'destination': { 'type': 'string', ... },   # obligatori
    'category':    { 'type': 'string', ... },   # opcional
}
'required': ['destination']
```

La SQL ha d'acceptar **`destination`** i opcionalment **`category`**. Si cal un paràmetre nou, documenta-ho i actualitza el SCHEMA (acord amb l'equip).

### 4.2 Explorar schema — preguntes a respondre

Obre `docs/schema.sql` i busca taules relacionades amb ofertes. Pregunta't:

1. Quina taula té el títol, descripció, slug, imatge?
2. Com s'emmagatzema la ubicació (municipi, comarca)? Taula apart? FK?
3. Quin camp indica «publicat» / «actiu»?
4. Com es filtra per categoria («Familiar», «Activitats»…)?
5. Quin índex / columna usar per ORDER BY (data, relevància)?

**Consell:** executa `SHOW TABLES LIKE '%ofert%';` o similar a staging si el schema exportat no és clar.

### 4.3 Esborrany SQL (substituir noms reals)

```sql
-- ESborrany — NOMÉS EXEMPLE, noms de taula inventats
SELECT
    o.id,
    o.tipus,
    o.titol_ca      AS title,
    u.nom           AS location,
    o.descripcio    AS description,
    o.slug,
    o.imatge_url    AS image
FROM ??? o
JOIN ??? u ON ???
WHERE o.publicat = 1
  AND (
        u.nom LIKE CONCAT('%', ?, '%')
     OR u.comarca LIKE CONCAT('%', ?, '%')
      )
  AND (? IS NULL OR o.categoria = ?)
ORDER BY o.updated_at DESC
LIMIT 20;
```

Prova amb:

```sql
-- Cas 1: Berguedà sense categoria
SET @destination = 'Berguedà';
SET @category = NULL;

-- Cas 2: Berguedà + Familiar
SET @category = 'Familiar';
```

### 4.4 Validar resultats (checklist per cas)

| Comprovació | Com |
|-------------|-----|
| Retorna files? | `SELECT` no buit per Berguedà |
| Títols coherents | Compareu amb https://www.femturisme.cat/ofertes?ubicacio=Berguedà |
| URL correcta | `https://www.femturisme.cat/ofertes/{slug}` obre la fitxa |
| Filtre categoria | Amb `Familiar`, menys o diferents files que sense filtre |
| Regles negoci | No surten esborranys / esborrats (si existeixen camps així) |
| Rendiment | `< 2 s` amb `EXPLAIN` raonable |

### 4.5 Documentar a sql-mapeo.md

Copia la SQL final, el mapatge columna → JSON i els casos de prova a la secció `search_experiences` del fitxer (veure plantilla).

---

## 5. Mapatge columna SQL → JSON (totes les tools)

El LLM rep **aquest format** (el mateix que dóna avui el scraping):

```json
{
  "id": "12345",
  "type": "oferta",
  "title": "Títol de la fitxa",
  "location": "Gósol, Berguedà",
  "description": "Text curt…",
  "url": "https://www.femturisme.cat/ofertes/el-slug",
  "image": "https://www.femturisme.cat/media/…/foto.jpg",
  "date": null
}
```

| Camp JSON | D'on surt (exemple) | Notes |
|-----------|---------------------|-------|
| `id` | `o.id` | string al JSON |
| `type` | `o.tipus` | |
| `title` | `o.titol_ca` | obligatori |
| `location` | JOIN ubicació | |
| `description` | `o.descripcio` | truncar si cal a Fase 3 |
| `url` | construir des de `slug` + prefix secció | **validar manualment** |
| `image` | `o.imatge_url` o taula media | URL absoluta |
| `date` | només events | veure `search_events` |

**Prefix URL per secció:**

| Tool | Prefix path |
|------|-------------|
| experiences | `/ofertes/` |
| accommodations | `/on-dormir/` (confirmar amb web) |
| events | `/agenda/` |
| routes | `/rutes/` |

---

## 6. Les 4 tools — resum per documentar

| Tool | Paràmetres LLM | Filtres SQL equivalents (pista scrape) | Particularitat |
|------|----------------|----------------------------------------|----------------|
| `search_experiences` | `destination`, `category?` | `ubicacio`, `tipus` | Categories tipus Familiar, Activitats… |
| `search_accommodations` | `destination`, `type?` | `ubicacio`, `tipus` | hotel, casa-rural, camping… |
| `search_events` | `destination`, `date_from?`, `date_to?` | `ubicacio`, `data_inici`, `data_fi` | Omplir camp `date` al JSON; avui scraping posa data a `location` |
| `search_routes` | `destination`, `type?` | `ubicacio`, `tipus` | A peu, Cultura, Bici… |

---

## 7. Regles de negoci habituals (confirmar al schema real)

Incloure a la SQL quan existeixin columnes equivalents:

```sql
-- Exemples típics — adaptar noms reals
AND o.publicat = 1
AND o.eliminat = 0
AND (o.data_fi IS NULL OR o.data_fi >= CURDATE())   -- vigència
AND o.idioma IN ('ca', 'all')                        -- si aplica
```

Documenta cada condició a sql-mapeo.md amb el **motiu** (p.ex. «mateix filtre que la llista pública PHP»).

---

## 8. Què NO és la Fase 2

| No fer | Per què |
|--------|---------|
| Crear tools noves | Les 4 ja existeixen |
| Escriure codi Python de repositoris | Això és Fase 3 |
| Deixar el LLM generar SQL | Annex D del pla |
| Replicar totes les combinacions de filtres de la web | v1: paràmetres del SCHEMA + criteris tous al LLM sobre `description` |
| Una query per pregunta d'usuari | Una query per **tool**, parametritzada |

---

## 9. Definition of done (Fase 2 tancada)

- [ ] `docs/sql-mapeo.md` té **4 seccions** completes (experiences, accommodations, events, routes).
- [ ] Cada secció té: taules, SQL final, mapatge JSON, regles negoci, ≥3 casos provats.
- [ ] Cada SQL executada amb èxit a **MySQL staging** (captura: nombre de files + 1 exemple títol).
- [ ] URLs de mostra obren fitxa correcta al navegador.
- [ ] SCHEMA de tools revisat (només si cal afegir/canviar paràmetres).
- [ ] Equip d'implementació (Fase 3) pot treballar **sense preguntar** quines taules usar.

---

## 10. Després de la Fase 2

Segueix la guia **[Fase 3 — Tools de catàleg amb MySQL](./fase-3-tools-mysql-ca.md)**: copiar SQL → repositoris Python → tests → refactor `execute()`.

---

## 11. Si et bloqueges

| Pregunta | Acció |
|----------|-------|
| No trobo la taula d'ofertes | Cerca a schema.sql: `ofert`, `experience`, `activitat`… Pregunta al mantenedor PHP |
| El scrape retorna 20 i la SQL 3 | Revisa filtres `publicat`, JOIN ubicació, LIKE vs `=` |
| No sé construir la URL | Obre una fitxa a la web, copia el path, relaciona amb `slug` / `id` |
| Cal filtrar «perros» / «niños» | **No** cal columna SQL a v1 — el LLM filtra sobre `description` del JSON |
| Schema diferent staging vs prod | Documenta i usa staging com a referència; alerta ops |

---

## 12. Referències

| Recurs | On |
|--------|-----|
| Tools i SCHEMA actuals | `app/services/tools/*.py` |
| Format JSON cards | `app/services/tools/scraper.py` → `extract_cards()` |
| Per què no text-to-SQL | `plan-integracion-ca.md` Annex D |
| Implementació codi | `fase-3-tools-mysql-ca.md` |
| Plantilla documentació | `sql-mapeo.md` |
