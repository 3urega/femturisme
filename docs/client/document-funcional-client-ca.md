# Document funcional per al client — Assistent de xat femturisme.cat

**Per a qui és aquest document:** responsables de projecte, producte i consultora **abans** d'entrar en detall tècnic o de programació.

**Definició del negoci femturisme (font de veritat):** [dominio-femturisme-ca.md](dominio-femturisme-ca.md)

**Documents relacionats:**

| Document | Per a qui | Contingut |
|----------|-----------|-----------|
| [dominio-femturisme-ca.md](dominio-femturisme-ca.md) | Tothom | Què és cada tipus de contingut a femturisme |
| **Aquest document** | Client / direcció de projecte | Què es farà, com es comportarà, exemples |
| [especificacio-funcional-ca.md](especificacio-funcional-ca.md) | Analista / QA | Requeriments numerats, casos d'ús, criteris d'acceptació |
| [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) | Programadors | APIs, bases de dades, desplegament |

---

## 1. Resum en una pàgina

Construirem un **assistent de xat** dins **femturisme.cat** (globus flotant).

L'usuari escriu en llenguatge natural — per exemple: *«Què fem aquest cap de setmana a l'Empordà?»* — i rep:

1. Una **resposta redactada** (català, castellà o anglès).
2. **Enllaços a pàgines de femturisme.cat**.

Darrere hi ha **dues famílies d'informació**:

| Família | Què conté |
|---------|-----------|
| **Catàleg web (MySQL)** | **6 buscadors:** establiments, articles, on anar, rutes, agenda, experiències |
| **Guies PDF** | Fulletons municipals que pengeu vosaltres |

L'usuari veu **un sol xat**; el sistema tria quin buscador (o quins) cal usar.

---

## 2. Què veurà l'usuari final

### 2.1 A femturisme.cat (visitant)

- Globus de xat, panell de conversa, respostes amb enllaços.
- Reinici de conversa; indicador «Cercant…» mentre consulta dades.

### 2.2 Panell intern (equip femturisme)

- Pujar PDFs, veure estat d'indexació, reindexar, provar cerca.
- El visitant **no puja PDFs** des del xat.

---

## 3. Què construirem — bloc a bloc

### 3.1 Xat integrat a la web (PHP + servei agent)

| Part | Qui |
|------|-----|
| Globus i panell a femturisme.cat | **PHP** |
| Interpretar preguntes i generar respostes | **Servei agent (Python)** |
| Connexió web ↔ agent (mateix domini) | **PHP** (proxy) + **Ops** |

---

### 3.2 Sis buscadors sobre el catàleg MySQL

No farem un cercador genèric sobre tota la base de dades. Farem **sis buscadors concrets**, cadascun amb consulta preparada i filtres controlats (zona, tipus, dates…).

#### A — Establiments (on dormir i on menjar)

| | |
|---|---|
| **Negoci** | Hotels, campings, restaurants, bars… per zona i tipus |
| **Exemples** | «Hotel a Girona», «On menjar a Berga» |
| **Buscador intern** | `search_establishments` |
| **Codi** | `EstablishmentsRepository` + SQL a taula **establiments** |

#### B — Articles / notícies

| | |
|---|---|
| **Negoci** | Articles sobre poblacions, esdeveniments, parcs naturals, temes del portal |
| **Exemples** | «Notícies del Parc Natural del Cadí», «Articles sobre la Patum» |
| **Buscador intern** | `search_articles` |
| **Codi** | `ArticlesRepository` |

#### C — On anar (poblacions i llocs)

| | |
|---|---|
| **Negoci** | Pobles i llocs per visitar, amb descripcions |
| **Exemples** | «Què veure a Besalú», «Pobles bonics a l'Empordà» |
| **Buscador intern** | `search_destinations` |
| **Codi** | `DestinationsRepository` |

#### D — Rutes

| | |
|---|---|
| **Negoci** | Itineraris a peu, bici, etc. |
| **Exemples** | «Ruta a peu al Pirineu» |
| **Buscador intern** | `search_routes` |
| **Codi** | `RoutesRepository` |
| **Web** | `/rutes` |

#### E — Agenda (esdeveniments de calendari)

| | |
|---|---|
| **Negoci** | Fires, concerts, festes amb data |
| **Exemples** | «Què fem aquest cap de setmana a l'Empordà?» |
| **Buscador intern** | `search_events` |
| **Codi** | `EventsRepository` |
| **Web** | `/agenda` |

#### F — Experiències (activitats promocionals)

| | |
|---|---|
| **Negoci** | Activitats que penja un establiment o una població (no és el mateix que l'agenda de calendari) |
| **Exemples** | «Dinar de Sant Valentí al Berguedà», «Arrossada popular a Olvan» |
| **Buscador intern** | `search_experiences` |
| **Codi** | `ExperiencesRepository` |

**Important:** **Agenda ≠ experiències.** L'agenda són esdeveniments de calendari; les experiències són propostes lligades a un negoci o municipi. Detall: [dominio-femturisme-ca.md](dominio-femturisme-ca.md) §3.1.

#### Resum 6 + 1

| Domini | Buscador | Repositori | BD |
|--------|----------|------------|-----|
| Establiments | `search_establishments` | `EstablishmentsRepository` | MySQL |
| Articles | `search_articles` | `ArticlesRepository` | MySQL |
| On anar | `search_destinations` | `DestinationsRepository` | MySQL |
| Rutes | `search_routes` | `RoutesRepository` | MySQL |
| Agenda | `search_events` | `EventsRepository` | MySQL |
| Experiències | `search_experiences` | `ExperiencesRepository` | MySQL |
| Guies PDF | `search_municipality_guides` | (servei RAG) | PostgreSQL |

El servei agent **només llegeix** MySQL (usuari restringit). Abans de programar cada buscador cal documentar taules i SQL (`sql-mapeo.md`).

---

### 3.3 Cercador de guies PDF

Igual que abans: fulletons municipals indexats; panell admin per pujar-los. Veure [dominio-femturisme-ca.md](dominio-femturisme-ca.md) §4.7.

---

### 3.4 Panell d'administració de PDFs

Pujar, llistar, reindexar, provar cerca — panell intern al servei Python (`/admin/guides`).

---

### 3.5 Combinació automàtica (un sol xat)

| Pregunta | Buscadors probables |
|----------|---------------------|
| «Què fem aquest cap de setmana a l'Empordà?» | Agenda + opcionalment experiències o on anar |
| «Hotel i ruta a peu al Berguedà» | Establiments + Rutes |
| «Arrossada a Olvan i on dormir» | Experiències + Establiments |
| «Què fer avui a Berga i on dinar segons la guia?» | Agenda + Guia PDF |

---

## 4. Exemple: cap de setmana a l'Empordà

**Pregunta:** «Què fem aquest cap de setmana a l'Empordà?»

1. Entén destinació *Empordà* i dates del cap de setmana.
2. Consulta **agenda** (`search_events`).
3. Pot afegir **experiències** o **on anar** si enriqueix la resposta.
4. Redacta resposta amb enllaços a `femturisme.cat/agenda/...` (i altres seccions si cal).

---

## 5. Què toca cada equip

| Equip | Què farà |
|-------|----------|
| **PHP** | Globus, panell, proxy, reinici conversa |
| **Python** | 6 buscadors MySQL + guies PDF + panell admin |
| **Ops** | MySQL read-only, PostgreSQL, Docker, xarxa |
| **Femturisme** | Validar respostes; PDFs de prova; aclarir schema MySQL (preguntes obertes al doc de domini) |

---

## 6. Infraestructura mínima

MySQL (catàleg, lectura) + PostgreSQL (PDFs) + servei Python + APIs de llenguatge i embeddings.

Diagrama: [assets/diagrama-arquitectura-logica.png](assets/diagrama-arquitectura-logica.png).

---

## 7. Abast v1

### Inclòs

- Xat a femturisme.cat.
- **6 buscadors** de catàleg + **guies PDF**.
- Panell admin PDFs.
- Respostes amb enllaços; català, castellà, anglès.

### No inclòs

- Edició CMS des del xat; SQL lliure; GPS; panell admin dins PHP.

---

## 8. UAT simplificat

| # | Prova | Resultat esperat |
|---|-------|------------------|
| 1 | Globus visible (desktop + mòbil) | OK |
| 2 | «Hotel a Girona» | Enllaç establiment / on dormir |
| 3 | «Restaurant a Pals» | Enllaç establiment / on menjar |
| 4 | «Què fem aquest cap de setmana a l'Empordà?» | Enllaç(s) agenda Empordà |
| 5 | «Arrossada a Olvan» | Enllaç experiència rellevant |
| 6 | «Què veure a Besalú» | Enllaç població / on anar |
| 7 | «Notícies Parc Natural Cadí» | Enllaç article |
| 8 | «Ruta a peu Pirineu» | Enllaç `/rutes/...` |
| 9 | PDF indexat + pregunta guia | Resposta citant guia |
| 10 | Pregunta mixta (agenda + guia) | Resposta combinada |

---

## 9. Ordre lògic de treball

1. Infraestructura (MySQL read-only, PostgreSQL, Python).
2. Xat bàsic.
3. Documentar i implementar **6 buscadors** (un repositori + SQL cadascun).
4. Globus a femturisme.cat.
5. Panell PDFs + indexació (paral·lel).
6. Cercador guies.
7. ~30 converses de prova.

---

## 10. Glossari breu

Veure també [dominio-femturisme-ca.md](dominio-femturisme-ca.md) §3.

| Terme | Significat |
|-------|------------|
| **Buscador** | Funció per cercar en un domini concret (establiments, agenda…) |
| **Repositori** | Mòdul de codi amb la consulta MySQL d'un buscador |
| **Agenda** | Esdeveniments de calendari |
| **Experiència** | Activitat promocional d'un establiment o població |
| **Establiment** | Negoci on dormir o menjar |

---

## 11. Següent lectura

- [dominio-femturisme-ca.md](dominio-femturisme-ca.md) — definició completa del negoci
- [especificacio-funcional-ca.md](especificacio-funcional-ca.md) — requeriments i UAT formal
- [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) — implementació
