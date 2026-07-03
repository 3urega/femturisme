# Domini femturisme — Model de negoci per a l'agent de xat

**Font de veritat** sobre el que és femturisme.cat des del punt de vista de l'assistent conversacional.

| Camp | Valor |
|------|-------|
| **Versió** | 1.1 |
| **Data** | 2026-06-28 |
| **Canvi respecte v1.0** | Catàleg ampliat de 4 a **6 buscadors** MySQL (+ guies PDF) |
| **Documents derivats** | [document-funcional-client-ca.md](document-funcional-client-ca.md), [especificacio-funcional-ca.md](especificacio-funcional-ca.md), [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md), [sql-mapeo.md](sql-mapeo.md) |

---

## 1. Propòsit i audiència

Aquest document descriu **el negoci femturisme** tal com l'agent de xat ha d'entendre'l:

- Quines **fonts d'informació** existeixen.
- Què distingeix **agenda**, **experiències**, **establiments**, etc.
- Com es mapen (preliminarment) a MySQL i al codi.

**Audiència:** client, producte, analista, desenvolupadors abans d'estimar o programar.

Els altres documents **enllacen aquí** i no redefineixen el domini.

---

## 2. Visió general

L'agent consulta **7 fonts** en total:

| # | Font | BD | Descripció breu |
|---|------|-----|-----------------|
| 1 | **Establiments** | MySQL | On dormir i on menjar (mateixa entitat, filtre per tipus) |
| 2 | **Articles / notícies** | MySQL | Contingut editorial sobre poblacions, esdeveniments, parcs naturals… |
| 3 | **On anar** | MySQL | Pobles i poblacions amb descripcions turístiques |
| 4 | **Rutes** | MySQL | Itineraris (a peu, bici, etc.) |
| 5 | **Agenda** | MySQL | Esdeveniments de calendari (fires, concerts, festes…) |
| 6 | **Experiències** | MySQL | Activitats promocionals lligades a establiment o població |
| 7 | **Guies PDF** | PostgreSQL | Fulletons municipals indexats (cerca semàntica) |

```mermaid
flowchart TB
  subgraph mysql [MySQL femturisme read-only]
    EST[Establiments]
    ART[Articles]
    DEST[On anar / poblacions]
    RUT[Rutes]
    AGD[Agenda]
    EXP[Experiencies]
  end
  subgraph agent [Servei agent Python]
    T1[search_establishments]
    T2[search_articles]
    T3[search_destinations]
    T4[search_routes]
    T5[search_events]
    T6[search_experiences]
    T7[search_municipality_guides]
  end
  subgraph pg [PostgreSQL agent]
    PDF[Guies PDF + vectors]
  end
  EST --> T1
  ART --> T2
  DEST --> T3
  RUT --> T4
  AGD --> T5
  EXP --> T6
  PDF --> T7
```

---

## 3. Distincions crítiques de negoci

### 3.1 Agenda vs experiències

| | **Agenda** (`search_events`) | **Experiències** (`search_experiences`) |
|---|------------------------------|----------------------------------------|
| **Què és** | Esdeveniment de **calendari** (data concreta o interval) | Activitat **promocional** que penja d'un establiment o d'una població |
| **Exemples** | Fira medieval, concert, festa major | Dinar de Sant Valentí en un restaurant; arrossada popular a Olvan |
| **Pregunta típica** | «Què fem aquest cap de setmana a l'Empordà?» | «Quina arrossada hi ha a Olvan?» |
| **Filtres clau** | Destinació + **dates** | Destinació + categoria; opcional establiment/població |
| **Secció web** | `/agenda` | TBD (hipòtesi: `/ofertes` o secció pròpia — confirmar amb schema) |

**No confondre:** l'antic model anomenava «ofertes» com `search_experiences`. En el model nou, **experiències** té el significat de negoci descrit pel client (activitat lligada a establiment/població).

### 3.2 Establiments: dormir + menjar

| | Detall |
|---|--------|
| **Entitat** | **Establiment** (taula d'establiments al CMS) |
| **Tipus** | Hotel, camping, restaurant, bar, etc. — filtre per **tipus** |
| **Un sol buscador** | `search_establishments` (no dos buscadors separats) |
| **Preguntes** | «On dormir a Girona», «Restaurant a Pals», «On menjar al Berguedà» |

Substitueix l'antic `search_accommodations` (només allotjament).

### 3.3 On anar vs establiments vs articles

| Domini | Contingut |
|--------|-----------|
| **On anar** | Fitxa de **població** o lloc: descripció, què veure, context territorial |
| **Establiments** | Negoci concret on dormir o menjar |
| **Articles** | Notícia o article sobre un tema (parcs naturals, esdeveniments, consells…) |

---

## 4. Catàleg per domini

### 4.1 Establiments (on dormir i on menjar)

| Camp | Valor |
|------|-------|
| **Descripció** | Cerca d'establiments turístics per zona i tipus (allotjament, restauració…). |
| **Exemples de preguntes** | «Hotel a Girona», «Camping Costa Brava», «On menjar a Berga», «Restaurant romàntic Empordà» |
| **Tool** | `search_establishments` |
| **Repository** | `EstablishmentsRepository` |
| **Paràmetres v1** | `destination` (required), `type` (optional: hotel, camping, restaurant…) |
| **Secció web** | `/on-dormir`, `/on-menjar` o llistat unificat d'establiments — **TBD** |
| **URL fitxa** | TBD segons tipus (p.ex. `/on-dormir/{slug}`, `/on-menjar/{slug}`) |
| **Taules MySQL** | **TBD** — hipòtesi: taula `establiments` + relació tipus + ubicació |
| **Relacions** | Experiències poden referenciar un establiment |

---

### 4.2 Articles / notícies

| Camp | Valor |
|------|-------|
| **Descripció** | Articles o notícies sobre poblacions, esdeveniments, parcs naturals, temes diversos del portal. |
| **Exemples de preguntes** | «Notícies sobre el Parc Natural del Cadí», «Articles sobre la Patum de Berga», «Què escriu femturisme sobre Cadaqués» |
| **Tool** | `search_articles` |
| **Repository** | `ArticlesRepository` |
| **Paràmetres v1** | `destination` (optional), `topic` (optional), `query` (optional, text lliure curt) |
| **Secció web** | **TBD** (blog, notícies, secció editorial) |
| **URL fitxa** | **TBD** |
| **Taules MySQL** | **TBD** — hipòtesi: `articles`, `noticies`, o equivalent legacy |
| **Relacions** | Pot mencionar poblacions, esdeveniments, parcs; no substitueix agenda ni on anar |

---

### 4.3 On anar (poblacions i llocs)

| Camp | Valor |
|------|-------|
| **Descripció** | Informació sobre **pobles, municipis o llocs** per visitar: descripcions, context, què hi trobarà el visitant. |
| **Exemples de preguntes** | «Què veure a Besalú», «Com és visitar Pals», «Pobles bonics a l'Empordà» |
| **Tool** | `search_destinations` |
| **Repository** | `DestinationsRepository` |
| **Paràmetres v1** | `destination` (required), `region` (optional) |
| **Secció web** | **TBD** — secció «on anar» o fitxes de població |
| **URL fitxa** | **TBD** |
| **Taules MySQL** | **TBD** — hipòtesi: taules de poblacions/municipis + camps descriptius |
| **Relacions** | Complementa agenda, rutes i establiments (context territorial) |

---

### 4.4 Rutes

| Camp | Valor |
|------|-------|
| **Descripció** | Itineraris turístics per zona i modalitat. |
| **Exemples de preguntes** | «Ruta a peu al Pirineu», «Ruta en bici per l'Empordà», «Senderisme Berguedà» |
| **Tool** | `search_routes` |
| **Repository** | `RoutesRepository` |
| **Paràmetres v1** | `destination` (required), `type` (optional: a peu, bici…) |
| **Secció web** | `/rutes` |
| **URL fitxa** | `https://www.femturisme.cat/rutes/{slug}` |
| **Taules MySQL** | **TBD** — confirmar amb schema (similar al model anterior) |
| **Relacions** | Sovint vinculades a comarques o pobles de «on anar» |

---

### 4.5 Agenda (esdeveniments de calendari)

| Camp | Valor |
|------|-------|
| **Descripció** | Esdeveniments amb data: fires, concerts, festes, activitats programades al calendari públic. |
| **Exemples de preguntes** | «Què fem aquest cap de setmana a l'Empordà?», «Agenda Barcelona aquest mes», «Festes majors al Berguedà» |
| **Tool** | `search_events` |
| **Repository** | `EventsRepository` |
| **Paràmetres v1** | `destination` (required), `date_from`, `date_to` (optional) |
| **Secció web** | `/agenda` |
| **URL fitxa** | `https://www.femturisme.cat/agenda/{slug}` |
| **Taules MySQL** | **TBD** — confirmar regles vigència/publicació |
| **Relacions** | Distint d'experiències (§3.1) |

---

### 4.6 Experiències (activitats promocionals)

| Camp | Valor |
|------|-------|
| **Descripció** | Activitats que un **establiment** o una **població** «penja» com a proposta concreta (sovint amb acció comercial o promocional). |
| **Exemples de preguntes** | «Dinar de Sant Valentí al Berguedà», «Arrossada popular a Olvan», «Experiències en família a la Cerdanya» |
| **Tool** | `search_experiences` |
| **Repository** | `ExperiencesRepository` |
| **Paràmetres v1** | `destination` (required), `category` (optional), `establishment` (optional) |
| **Secció web** | **TBD** — pot coincidir parcialment amb `/ofertes` legacy |
| **URL fitxa** | **TBD** |
| **Taules MySQL** | **TBD** — relació amb establiments i/o poblacions |
| **Relacions** | Anchor: establiment o població; no substituir agenda |

---

### 4.7 Guies PDF (domini 7)

| Camp | Valor |
|------|-------|
| **Descripció** | Fulletons municipals pujats per l'equip femturisme; cerca semàntica dins el text. |
| **Exemples de preguntes** | «On dinar a Berga segons la guia?», «On aparcar segons el fulletó» |
| **Tool** | `search_municipality_guides` |
| **Dades** | PostgreSQL + vectors (no MySQL) |
| **Paràmetres v1** | `query` (required), `municipality` (required), `category` (optional) |
| **Administració** | Panell `/admin/guides` |

Veure [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) §6 per pipeline d'indexació.

---

## 5. Matriu de mapatge

| Domini negoci | Tool | Repository | BD | Estat schema |
|---------------|------|------------|-----|--------------|
| Establiments (dormir/menjar) | `search_establishments` | `EstablishmentsRepository` | MySQL | TBD |
| Articles / notícies | `search_articles` | `ArticlesRepository` | MySQL | TBD |
| On anar | `search_destinations` | `DestinationsRepository` | MySQL | TBD |
| Rutes | `search_routes` | `RoutesRepository` | MySQL | TBD |
| Agenda | `search_events` | `EventsRepository` | MySQL | TBD |
| Experiències | `search_experiences` | `ExperiencesRepository` | MySQL | TBD |
| Guies PDF | `search_municipality_guides` | (servei RAG) | PostgreSQL | Definit a pla Fase 5 |

---

## 6. Mapatge des del model antic (4 tools)

Documentació i prototip anterior (scraping) usaven **4 buscadors**. Mapatge de migració:

| Model antic (v1.0 docs) | Model nou (v1.1) | Acció |
|---------------------------|------------------|-------|
| `search_accommodations` | **`search_establishments`** | Fusionar dormir + menjar; filtre `type` |
| `search_experiences` (secció `/ofertes`) | **`search_experiences`** (redefinit) | Canvi de significat: activitats promocionals |
| `search_events` | **`search_events`** | Mateix nom; definició reforçada (agenda) |
| `search_routes` | **`search_routes`** | Mateix nom |
| — | **`search_articles`** | **Nou** |
| — | **`search_destinations`** | **Nou** |

**Codi actual** ([app/services/tools/](../app/services/tools/)): encara implementa el model antic (4 tools + scraping). **Objectiu v1:** 6 tools + MySQL segons aquest document.

---

## 7. Preguntes obertes (pendents de schema MySQL)

Cal resoldre amb el mantenedor PHP / export `docs/schema.sql`:

| # | Pregunta |
|---|----------|
| Q-01 | Nom exacte de la taula d'**establiments** i com es distingeix tipus dormir vs menjar |
| Q-02 | On viuen **articles/notícies** i quins camps retornar (títol, resum, slug, data) |
| Q-03 | Taula(s) de **poblacions / on anar** i relació amb comarques |
| Q-04 | Taula i relacions d'**experiències** vs agenda (FK a establiment/població?) |
| Q-05 | URL canònica per experiències i articles |
| Q-06 | Regles `publicat`, dates vigents, idioma per a cada entitat |
| Q-07 | Límits de JOINs legacy (`rel_*`, noms críptics) per a cada buscador |

Respostes aniran a [sql-mapeo.md](sql-mapeo.md) (Fase 2).

---

## 8. Estat implementació: actual vs objectiu

| Component | Avui (prototip) | Objectiu v1 |
|-----------|-----------------|-------------|
| Tools catàleg | 4 (`experiences`, `accommodations`, `events`, `routes`) | **6** (veure §5) |
| Font de dades catàleg | Scraping HTML femturisme.cat | **MySQL read-only** |
| Guies PDF | Stub / parcial | Pipeline + `search_municipality_guides` |
| `sql-mapeo.md` | Plantilla 4 tools | **6 tools** (SQL TODO) |

---

## 9. Referències

| Document | Ús |
|----------|-----|
| [document-funcional-client-ca.md](document-funcional-client-ca.md) | Què es construirà (llenguatge client) |
| [especificacio-funcional-ca.md](especificacio-funcional-ca.md) | Requeriments i UAT |
| [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) | APIs, JSON, desplegament |
| [sql-mapeo.md](sql-mapeo.md) | SQL per tool (Fase 2–3) |
| [plan-integracion-ca.md](plan-integracion-ca.md) | Pla intern per fases |
