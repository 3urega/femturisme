# AGENTS.md — Guia per a agents i desenvolupadors

Instruccions per **planificar** i **implementar** canvis al projecte **agent_femturisme** (assistent de xat per a femturisme.cat).

Abans de proposar passos, escriure codi o documentació nova, **llegeix els documents indicats** segons el tipus de feina.

**Estat del projecte:** mantén actualitzat [docs/devs/checklist-entrega.md](docs/devs/checklist-entrega.md) — veure **§11** (lectura i marcatge automàtic per agents).

---

## 1. Què és aquest projecte

Servei **Python (Flask)** amb LLM i buscadors parametritzats que alimenten un **xat** integrat a femturisme.cat (via PHP + proxy).

| Capa | Tecnologia | Rol |
|------|------------|-----|
| Catàleg web | **MySQL** (read-only) | 6 buscadors sobre contingut existent |
| Guies PDF | **PostgreSQL** + pgvector | Indexació i cerca semàntica |
| Xat públic | **PHP** + JS | Widget, proxy `/api/chat` |
| Agent | **Python** | API, tools, panell admin PDFs |

**Estat codi vs documentació:** el prototip encara té **4 tools legacy** amb scraping; la documentació v1.1 defineix **6 buscadors MySQL + guies PDF**. Prioritza sempre la documentació de domini com a objectiu.

---

## 2. Mapa de documents (què llegir i quan)

### 2.1 Jerarquia — no saltar nivells

```
docs/client/dominio-femturisme-ca.md     ← negoci (SEMPRE primer)
        ↓
docs/client/document-funcional-client-ca.md   ← què es construeix (client)
        ↓
docs/client/especificacio-funcional-ca.md     ← RF, CU, CA, UAT
        ↓
docs/client/tecnic.md                       ← APIs, repos, desplegament (v2.1)
        ↓
docs/devs/checklist-entrega.md              ← ROADMAP EXECUTABLE (llegir + actualitzar)
        ↓
docs/arquitectura/                          ← OBLIGATORI abans de codi Python nou
        ↓
docs/sql-mapeo.md                           ← SQL concreta per buscador
```

### 2.2 Documents per tipus de tasca

| Si estàs… | Llegeix (en ordre) |
|-----------|-------------------|
| **Planificant qualsevol feature** | [dominio-femturisme-ca.md](docs/client/dominio-femturisme-ca.md) → [docs/devs/checklist-entrega.md](docs/devs/checklist-entrega.md) (pas obert) → docs client |
| **Implementant codi Python (qualsevol)** | [docs/arquitectura/index.md](docs/arquitectura/index.md) → [capas-y-modulos.md](docs/arquitectura/capas-y-modulos.md) → [patrones-y-convenciones.md](docs/arquitectura/patrones-y-convenciones.md) → [docs/devs/testing.md](docs/devs/testing.md) |
| **Implementant un buscador de catàleg** | domini → [tecnic.md](docs/client/tecnic.md) §6 → arquitectura → [sql-mapeo.md](docs/sql-mapeo.md) → [fase-3-tools-mysql-ca.md](docs/fase-3-tools-mysql-ca.md) |
| **Implementant guies PDF / RAG** | domini §4.7 → [postgre_schema.md](docs/postgre_schema.md) → especificació tècnica §6–7 → [plan-integracion-ca.md](docs/plan-integracion-ca.md) Fases 5–6 |
| **Integrant widget PHP / proxy** | [document-funcional-client-ca.md](docs/client/document-funcional-client-ca.md) §3.1 → especificació tècnica §3–4 → [especificacio-funcional-ca.md](docs/client/especificacio-funcional-ca.md) RF-01xx |
| **Depurant l'agent / SSE / LLM** | [agente.md](docs/agente.md) → [app/services/agent_service.py](app/services/agent_service.py) |
| **Entendre el prototip scraping (legacy)** | [scraping-y-respuestas.md](docs/scraping-y-respuestas.md) — **no** és l'objectiu v1 |
| **Decidir SQL lliure vs tools** | [text-to-sql-desventajas.md](docs/text-to-sql-desventajas.md) — decisió tancada: **tools parametritzades** |
| **Roadmap per fases complet** | [plan-integracion-ca.md](docs/plan-integracion-ca.md) (nota: alguns apartats encara mencionen 4 tools; domini fa fe) |
| **Índex general docs** | [docs/index.md](docs/index.md) |
| **Checklist entrega (devs)** | [docs/devs/checklist-entrega.md](docs/devs/checklist-entrega.md) |
| **Tests** | [docs/devs/testing.md](docs/devs/testing.md) |
| **Issues GitHub (workflow agent)** | `.cursor/skills/plan-to-issues` → `publish-github-issues` → `kanban-board` |

### 2.3 Diagrama de domini (referència ràpida)

Font: [docs/assets/diagrama-dominio-cataleg.mmd](docs/assets/diagrama-dominio-cataleg.mmd) · Arquitectura: [docs/assets/diagrama-arquitectura-logica.mmd](docs/assets/diagrama-arquitectura-logica.mmd)

---

## 3. Els 6 buscadors + PDF (objectiu v1)

Consulta [dominio-femturisme-ca.md](docs/client/dominio-femturisme-ca.md) §5 abans d'afegir o modificar una tool.

| Domini | Tool | Repository (objectiu) |
|--------|------|------------------------|
| Establiments (dormir/menjar) | `search_establishments` | `EstablishmentsRepository` |
| Articles / notícies | `search_articles` | `ArticlesRepository` |
| On anar | `search_destinations` | `DestinationsRepository` |
| Rutes | `search_routes` | `RoutesRepository` |
| Agenda | `search_events` | `EventsRepository` |
| Experiències promocionals | `search_experiences` | `ExperiencesRepository` |
| Guies PDF / entitats | `search_entity_knowledge` | `DocumentsRepository` + PostgreSQL |

**Regles de negoci crítiques:**

- **Agenda ≠ experiències** (RN-009 al funcional).
- **Dormir + menjar** = un buscador (`search_establishments`), filtre per `type`.
- **No** SQL generada per LLM en producció.
- MySQL **només lectura** des de l'agent.
- Respostes amb **enllaços** a femturisme.cat quan hi ha resultats de catàleg.

---

## 4. Workflow: nova feature

### Pas 0 — Classificar la feature

| Tipus | Exemple | Documents clau |
|-------|---------|------------------|
| **A** Nou/ampliar buscador catàleg | Afegir filtre a agenda | domini, sql-mapeo, fase-2/3 |
| **B** Guies PDF / admin | Reindexar, smoke test | plan Fase 5, espec. tècnica §6–7 |
| **C** Xat / UI / PHP | Globus, proxy, page_context | funcional RF-01xx, espec. tècnica §3 |
| **D** Agent / prompt / routing | Multi-tool, idiomes | agente.md, espec. funcional RF-02xx |
| **E** Infra / ops | Docker, PostgreSQL, `.env` | espec. tècnica §8–10, plan Fase 0 |

### Pas 1 — Planificació (abans de codi)

1. Obre **[docs/devs/checklist-entrega.md](docs/devs/checklist-entrega.md)** i identifica el(s) pas(s) `DEV-xxx` que aquesta feature completa o desbloqueja. Menciona'ls al pla.
2. Llegeix **dominio-femturisme-ca.md**: la feature encaixa en algun dels 6 dominis (+ PDF)?
3. Si afecta comportament observable → revisa **requeriments.md** / **funcional.md** (RF/CA); proposa nous IDs si cal.
4. Si afecta API, SQL o repos → revisa **tecnic.md** i **sql-mapeo.md**.
5. Comprova si el codi actual és **legacy** (4 tools + scraping a [app/services/tools/](app/services/tools/)).
6. Escriu un pla curt: fitxers a tocar, dependències, criteris d'acceptació (CA) aplicables, IDs `DEV-xxx` afectats.

### Pas 2 — Implementació

**Abans de tocar codi:** llegeix [docs/arquitectura/patrones-y-convenciones.md](docs/arquitectura/patrones-y-convenciones.md) i comprova [estado-actual-vs-objetivo.md](docs/arquitectura/estado-actual-vs-objetivo.md) per no copiar patrons legacy (scraping, estat global).

**Buscador de catàleg (tipus A):**

1. Completar secció a `docs/sql-mapeo.md` (taules, SQL, mapatge JSON, casos prova).
2. Crear/actualitzar `app/db/repositories/<Nom>Repository.py`.
3. Crear/actualitzar `app/services/tools/<nom>.py` amb SCHEMA + `execute()`.
4. Registrar a [app/services/tools/__init__.py](app/services/tools/__init__.py) → `ALL_TOOLS`.
5. Proves segons CA a especificació funcional §9.2.

**No** ampliar scraping com a solució permanent; és prototip.

### Pas 3 — Tancament

- [ ] Comportament alineat amb domini (no confondre agenda/experiències/establiments).
- [ ] JSON de sortida segons tecnic.md §6.13 (card + wrapper).
- [ ] CA/UAT aplicables verificables.
- [ ] Si canvia l'abast funcional → actualitzar docs `docs/client/` i, si cal, `sql-mapeo.md`.
- [ ] **Actualitzar [checklist-entrega.md](docs/devs/checklist-entrega.md)** — veure §11.
- [ ] No commit unless user asks.

---

## 5. Ubicació del codi

| Àrea | Ruta |
|------|------|
| API xat | [app/routes/api.py](app/routes/api.py) |
| Bucle agent | [app/services/agent_service.py](app/services/agent_service.py) |
| LLM providers | [app/services/llm_service.py](app/services/llm_service.py) |
| Tools (legacy 4) | [app/services/tools/](app/services/tools/) |
| Scraping prototip | [app/services/tools/scraper.py](app/services/tools/scraper.py) |
| Repositories (objectiu) | `app/db/repositories/` (crear segons fase-3) |
| Chat UI | [app/static/js/chat.js](app/static/js/chat.js) |
| Config | [app/config.py](app/config.py) |

---

## 6. Constraints (no negociables v1)

1. **6 buscadors parametritzats** + `search_entity_knowledge` — no text-to-SQL al xat de producció.
2. **MySQL read-only** (`agent_read`); agent no escriu al CMS.
3. **Un sol xat** per al visitant; combinació automàtica de buscadors.
4. **Enllaços** a femturisme.cat a les respostes de catàleg.
5. **Guies PDF** només via panell admin intern; visitant no puja PDFs.
6. **Idiomes:** ca / es / en segons pregunta de l'usuari.
7. **RAG en femturisme.cat:** Fase 1 sense RAG; Fase 2 només si `results[].entity_id` — veure [funcional.md](docs/client/funcional.md) §8.4.

---

## 7. Legacy vs objectiu (evitar confusions)

| Legacy (codi/docs antics) | Objectiu v1.1 |
|---------------------------|---------------|
| `search_accommodations` | `search_establishments` |
| `search_experiences` = ofertes web | `search_experiences` = promocionals |
| 4 tools | 6 tools |
| Scraping HTML | MySQL via repositories |
| [scraping-y-respuestas.md](docs/scraping-y-respuestas.md) | [sql-mapeo.md](docs/sql-mapeo.md) |

---

## 8. Preguntes obertes de schema

Abans d'implementar SQL definitiva, revisar **dominio-femturisme-ca.md §7** i confirmar amb `docs/schema.sql` (quan existeixi). Fins llavors, marcar TBD a `sql-mapeo.md`.

---

## 9. Idioma i to

- **Documentació de producte/domini:** català (`docs/client/`).
- **Codi i comentaris:** seguir l'anglès/català ja present als fitxers existents.
- **Respostes al usuari final del xat:** idioma de la pregunta.

---

## 10. Checklist ràpid per a l'agent

Abans de proposar un pla o escriure codi:

- [ ] He llegit **dominio-femturisme-ca.md** per aquesta feature?
- [ ] He obert **docs/devs/checklist-entrega.md** i identificat el pas `DEV-xxx` obert?
- [ ] He llegit **docs/arquitectura/** abans d'escriure codi Python?
- [ ] Sé si és catàleg (quina tool?), PDF, PHP o infra?
- [ ] He comprovat **sql-mapeo.md** / tecnic.md per contracte JSON i paràmetres?
- [ ] La feature respecta agenda ≠ experiències i establiments unificats?
- [ ] He identificat CA aplicables (requeriments.md §12)?
- [ ] No estic perpetuant scraping quan tocava MySQL?

---

## 11. Checklist d'entrega — obligatori per agents

Font: **[docs/devs/checklist-entrega.md](docs/devs/checklist-entrega.md)** (90 passos `DEV-001`…`DEV-904`).

Aquest fitxer és l'estat viu del projecte. **No és només documentació:** cal llegir-lo i mantenir-lo actualitzat en cada sessió de treball.

### Quan llegir (automàtic)

| Moment | Acció |
|--------|--------|
| **Inici de qualsevol tasca d'implementació o planificació** | Llegir checklist; localitzar `DEV-xxx` relacionats; citar-los al pla |
| **Usuari demana «on som» / estat del projecte** | Llegir checklist; informar progrés `X / 90` i pròxims passos oberts |
| **Després d'implementar codi, docs o infra** | Revisar criteris **Detect** dels `DEV-xxx` tocats |
| **Tancar issue GitHub** (skill kanban-board) | Marcar checkboxes + actualitzar comptador |
| **Auditoria de sessió** (opcional, si l'usuari no ha demanat res concret) | Escanejar repo vs **Detect** de items `[ ]` de la fase actual |

### Quan marcar `- [x]` (automàtic)

1. Comprova el criteri **Detect** del pas (fitxer existeix, test passa, endpoint respon, doc complet…).
2. Canvia `- [ ]` → `- [x]` a `docs/devs/checklist-entrega.md`.
3. Opcional: afegeix data al final de la línia, p.ex. `*(2026-07-03)*`.
4. **Recalcula el comptador** del capçalera: `**Progrés:** X / 90 completats`.
5. Actualitza `**Última actualització:**` amb la data d'avui.

**No marcar** si: només prototip parcial, encara hi ha TODO, scraping quan tocava MySQL, o el **Detect** no es compleix literalment.

### Mapatge ràpid feature → DEV

| Àrea | IDs checklist |
|------|----------------|
| Docs / preparació | DEV-001…011 |
| Pre-requisits client | DEV-020…027 |
| Servei Flask base | DEV-100…109 |
| MySQL / sql-mapeo | DEV-200…208, DEV-010 |
| Buscador concret | DEV-301…306 (un per domini) |
| Integració PHP | DEV-400…406 |
| RAG / PostgreSQL | DEV-500…507 |
| Entrega Fase 1 | DEV-600…607 |
| Fase 2 entitats | DEV-700…707 |
| Ops / producció | DEV-800…805 |
| Entrega final | DEV-900…904 |

### Exemple de flux agent

```text
Usuari: «Implementa ExperiencesRepository»
  → Llegeix checklist → pas obert DEV-301
  → Pla citant DEV-301 + sql-mapeo + arquitectura
  → Implementa + pytest passa
  → Marca DEV-301 [x], progrés 15/90
  → Informa usuari què queda obert (DEV-302…)
```

Veure instruccions detallades: [docs/devs/index.md](docs/devs/index.md).
