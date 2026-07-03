# Plan de integración

Plan maestro por fases. Objetivo: **chat embebido en femturisme.cat** alimentado por un **servicio agente Python** con acceso **MySQL** (catálogo) y **vector store** (guías PDF), en un **único widget** para el usuario.

Arquitectura del agente (bucle tool use, LLM, SSE): [agente.md](./agente.md).

---

## Índice

1. [Visión y arquitectura objetivo](#1-visión-y-arquitectura-objetivo)
2. [Principios](#2-principios)
3. [Mapa de fases](#3-mapa-de-fases)
4. [Fase 0 — Infraestructura y accesos](#fase-0)
5. [Fase 1 — Servicio Python en servidor](#fase-1)
6. [Fase 2 — Exploración MySQL y diseño de queries](#fase-2)
7. [Fase 3 — Tools de catálogo con MySQL](#fase-3)
8. [Fase 4 — Widget en femturisme.cat](#fase-4)
9. [Fase 5 — Ingesta de PDFs y vector store](#fase-5)
10. [Fase 6 — Tool RAG (guías municipales)](#fase-6)
11. [Fase 7 — Chat unificado](#fase-7)
12. [Fase 8 — Producción y operaciones](#fase-8)
13. [Criterios de éxito](#13-criterios-de-éxito)
14. [Riesgos y decisiones pendientes](#14-riesgos-y-decisiones-pendientes)
15. [Anexo A — Checklist SQL por tool](#15-anexo-a--checklist-sql-por-tool)
16. [Anexo B — Contrato JSON hacia el LLM](#16-anexo-b--contrato-json-hacia-el-llm)
17. [Anexo C — Estructura de carpetas](#17-anexo-c--estructura-de-carpetas)
18. [Anexo D — Tools parametrizadas vs text-to-SQL](#anexo-d)

---

## 1. Visión y arquitectura objetivo

```
┌────────────────────────────────────────────────────────────────────────┐
│ femturisme.cat (PHP) — frontend público                                  │
│  • Globo flotante + panel chat (JS/CSS en layout global)               │
│  • page_context: sección, ubicación, municipio (desde URL)             │
│  • NO incluye subida de PDFs ni administración del agente              │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ POST /api/chat  (SSE, mismo dominio vía proxy)
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Servicio agente — Python (servidor dedicado / contenedor)              │
│  • API chat: AgentService + LLM + SSE                                  │
│  • Panel admin interno (Fase 5): /admin/guides — subida y estado PDFs │
│  • Tools catálogo → repositorios MySQL (read-only)                     │
│  • Tools guías     → vector store (PDFs indexados)                     │
└───────────────┬───────────────────────────────┬────────────────────────┘
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ MySQL femturisme           │   │ Vector store + BD agent    │
│ experiencias, agenda,      │   │ chunks, embeddings,        │
│ allotjaments, rutes…       │   │ guide_documents (estado PDF)│
└───────────────────────────┘   └───────────────────────────┘
```

**Dos frontends, dos roles:**

| Frontend | Dónde vive | Quién lo usa | Función |
|----------|------------|--------------|---------|
| **Widget de chat** | femturisme.cat (PHP + JS) | Visitantes de la web | Conversar con el agente |
| **Panel admin PDFs** | Servicio Python (`/admin/guides`) | Equipo femturisme (interno) | Subir guías, ver estado de indexación |

**Un solo chat** para el usuario final. El LLM elige tools de catálogo, de guías PDF, o ambas según la pregunta.

---

## 2. Principios

1. **Reutilizar el agente Python** — `AgentService`, `llm_service`, patrón SCHEMA + `execute()`.
2. **MySQL read-only** desde el servicio Python; el agente no escribe en BD.
3. **Queries diseñadas para el LLM** — campos, filtros y límites pensados para las tools, no para replicar pantallas PHP. Decisión detallada: [Anexo D](#anexo-d).
4. **Contrato JSON estable** entre repositorios y LLM (Anexo B).
5. **Catálogo y guías PDF** — fuentes y tools distintas; mismo endpoint `/api/chat`.
6. **PHP solo presenta el chat público** — layout, widget, contexto de página; no ejecuta el LLM ni gestiona PDFs.
7. **Panel admin en Python** — el servicio agente incluye una **UI interna mínima** (Fase 5) para operaciones (subir PDFs, ver estado). No hace falta tocar el CMS PHP de femturisme. Alternativa v1: solo CLI si se prefiere sin UI.

---

## 3. Mapa de fases

| Fase | Nombre | Depende de | Entregable |
|------|--------|------------|------------|
| **[0](#fase-0)** | [Infraestructura y accesos](#fase-0) | — | MySQL read-only, PostgreSQL agent, staging, `docs/schema.sql` |
| **[1](#fase-1)** | [Servicio Python en servidor](#fase-1) | [0](#fase-0) | Agente desplegado, `/api/chat` accesible en red interna |
| **[2](#fase-2)** | [Exploración MySQL y queries](#fase-2) | [0](#fase-0), [1](#fase-1) | `sql-mapeo.md` con queries por tool |
| **[3](#fase-3)** | [Tools catálogo + MySQL](#fase-3) | [2](#fase-2) | 4 tools operativas vía repositorios |
| **[4](#fase-4)** | [Widget en femturisme.cat](#fase-4) | [1](#fase-1), [3](#fase-3) | Globo + panel en web, proxy mismo dominio |
| **[5](#fase-5)** | [Ingesta PDF + vector store](#fase-5) | [0](#fase-0) | Panel admin, pipeline indexación, estado por documento |
| **[6](#fase-6)** | [Tool RAG guías](#fase-6) | [5](#fase-5) | `search_municipality_guides` operativa |
| **[7](#fase-7)** | [Chat unificado](#fase-7) | [3](#fase-3), [4](#fase-4), [6](#fase-6) | Un widget; catálogo + guías en producción |
| **[8](#fase-8)** | [Producción y ops](#fase-8) | [7](#fase-7) | Monitorización, límites, runbooks |

**Paralelismo recomendado:**

- Fases **2 y 3** (SQL) pueden avanzar en cuanto Fase 0–1 estén listas.
- Fase **5** (PDFs) puede ir en paralelo con Fases 2–4.
- Fase **4** (widget) requiere Fase 1; conviene tener al menos una tool MySQL en Fase 3 antes de producción.

```
Tiempo ───────────────────────────────────────────────────────────►

Fase 0 ████
Fase 1    ████
Fase 2      ██████████
Fase 3            ████████
Fase 4                  ██████        (widget; requiere agente + tools)
Fase 5      ████████████              (PDFs; paralelo)
Fase 6                        ██████
Fase 7                              ████
Fase 8                                  ████
```

---

## 4. Fase 0 — Infraestructura y accesos {#fase-0}

**Objetivo:** permisos, entornos y **dos bases de datos** documentadas y accesibles para que el equipo del agente pueda desarrollar **sin depender del mantenedor PHP** en el día a día.

| # | Tarea | Entregable concreto |
|---|-------|---------------------|
| 0.1 | Usuario MySQL **solo lectura** (catálogo femturisme) | Usuario `agent_read@<host>` con `SELECT` sobre tablas de contenido. Sin escritura. |
| 0.2 | Exportar **schema MySQL** | Archivo `docs/schema.sql` en **este repo** (`agent_femturisme`) |
| 0.3 | Acceso al **repo PHP de femturisme** (opcional) | Clone o lectura del código legacy solo si el schema no basta para entender JOINs |
| 0.4 | Entorno **staging** | MySQL + **PostgreSQL agent** accesibles; red/firewall hacia host Python |
| 0.5 | Decisión despliegue Python | Docker Compose / systemd / VM — diagrama con IP, puerto, quién despliega |
| 0.6 | Variables entorno | `.env.example`: `AGENT_*`, `MYSQL_*`, `POSTGRES_*` (o `AGENT_DB_*`), `VECTOR_*` |
| 0.7 | **BD agent PostgreSQL** | Instancia staging (y plan producción): host, puerto, nombre BD, backup acordado |
| 0.8 | Usuario BD agent | Usuario `agent_app@…` **read-write** solo sobre la BD del agent (no MySQL femturisme) |
| 0.9 | Decisión vector store | **pgvector** (misma PostgreSQL, recomendado) vs Qdrant + PostgreSQL — documentado antes Fase 5 |

### ¿Qué es el «schema» y por qué va en el repo del agente?

Aquí **schema** = **estructura de la base de datos MySQL de femturisme**, no código de aplicación.

Es un volcado **solo de DDL** (definición de tablas, columnas, índices, FKs), **sin filas de datos**:

```bash
mysqldump --no-data -h <host> -u <user> -p femturisme > docs/schema.sql
```

El archivo resultante contiene líneas del estilo `CREATE TABLE experiencies (...)` — sirve para ver qué tablas existen, cómo se relacionan y qué columnas hay **sin conectar a producción** cada vez que alguien del equipo abre el proyecto.

| Pregunta | Respuesta |
|----------|-----------|
| ¿De qué repo hablamos? | Del repo **nuevo del agente**: `agent_femturisme` (este proyecto Python). **No** del repo PHP de la web. |
| ¿Por qué commitearlo aquí? | Para que cualquier dev del agente tenga la estructura BD versionada en Git, pueda abrirla en DBeaver/Workbench offline y revisar PRs de Fase 2–3 sin VPN permanente. |
| ¿Sustituye a conectar a MySQL? | **No.** Sigue haciendo falta el usuario read-only (0.1) para probar queries con datos reales en staging. El schema es la **documentación estructural**; la conexión es la **validación con datos**. |
| ¿Quién lo genera y cuándo? | Ops o el mantenedor MySQL, **una vez al cerrar Fase 0** (y de nuevo cuando cambie el schema en producción). El dev del agente lo commitea en `docs/schema.sql`. |

### Repo PHP (tarea 0.3) — aclaración

Es **opcional** y **distinto** del schema:

- **Schema** → estructura de tablas (SQL estático en `docs/schema.sql`).
- **Repo PHP** → código fuente de femturisme.cat, útil solo si hay lógica de negocio enterrada en PHP (filtros de «publicado», JOINs raros) que no se deduce del `CREATE TABLE`.

Si el equipo PHP puede documentar reglas de negocio por escrito, el clone del repo PHP puede no ser necesario.

### BD propia del agent (PostgreSQL)

El agente necesita **una segunda base de datos**, independiente de la MySQL de femturisme. **No se puede reutilizar la MySQL read-only** para subir PDFs, guardar embeddings ni el estado de indexación.

```
Servicio Python (agente)
    │
    ├── MySQL femturisme (read-only)     → catálogo: ofertas, agenda, allotjaments, rutes
    │
    └── PostgreSQL agent (read-write)    → PDFs: guide_documents, chunks, embeddings (pgvector)
```

| Pregunta | Respuesta |
|----------|-----------|
| **¿Hace falta PostgreSQL?** | Hace falta una **BD propia del agent**. El plan recomienda **PostgreSQL** (con extensión **pgvector** si se acuerda en 0.9). |
| **¿Es la misma BD que femturisme?** | **No.** MySQL femturisme = datos del web (legacy). PostgreSQL agent = datos **solo del agente** (guías PDF, vectores, estado). |
| **¿Qué se guarda ahí?** | Tabla `guide_documents` (estado de cada PDF), chunks de texto, vectores de embedding (si pgvector), metadatos RAG. |
| **¿Dónde vive?** | Mismo servidor que Python (Docker Compose `app` + `postgres`), PostgreSQL gestionado (RDS, Supabase…) o VM interna — acordado con ops en 0.7. |
| **¿Quién la crea?** | Ops / equipo infra al cerrar Fase 0; el dev del agent configura conexión y migraciones (Fase 5). |
| **Staging vs producción** | **Dos instancias separadas** (o dos schemas/BDs): no indexar PDFs de prueba en producción. |

**Opciones de vector store (tarea 0.9):**

| Opción | BD agent | Dónde van los vectores | Notas |
|--------|----------|------------------------|-------|
| **A — recomendada v1** | PostgreSQL + pgvector | Misma PostgreSQL | Un solo servicio; menos piezas móviles |
| **B** | PostgreSQL (metadatos) | Qdrant (contenedor aparte) | Útil si ya tenéis Qdrant o PDFs muy grandes |
| **C — solo dev** | SQLite | Chroma local | No para producción; prototipo rápido |

**Variables de entorno** (añadir a `.env.example`, tarea 0.6):

```bash
# MySQL femturisme (read-only, catálogo)
MYSQL_HOST=...
MYSQL_USER=agent_read
MYSQL_PASSWORD=...
MYSQL_DATABASE=femturisme

# PostgreSQL agent (read-write, PDFs + vectores)
POSTGRES_HOST=...
POSTGRES_PORT=5432
POSTGRES_USER=agent_app
POSTGRES_PASSWORD=...
POSTGRES_DATABASE=agent_femturisme
# Si pgvector: misma URL; extensión CREATE EXTENSION vector; en la primera migración
```

**Docker Compose mínimo (ejemplo staging, tareas 0.5/0.7):**

```yaml
services:
  agent:
    build: .
    environment:
      MYSQL_HOST: ...
      POSTGRES_HOST: postgres
    depends_on: [postgres]
  postgres:
    image: pgvector/pgvector:pg16
    volumes: [agent_pg_data:/var/lib/postgresql/data]
    environment:
      POSTGRES_USER: agent_app
      POSTGRES_PASSWORD: ...
      POSTGRES_DB: agent_femturisme
```

**Checklist BD agent (ops + dev):**

- [ ] PostgreSQL staging levantado y accesible desde el host Python.
- [ ] Usuario `agent_app` con permisos solo sobre `agent_femturisme` (no superuser).
- [ ] Decisión 0.9 documentada (pgvector vs Qdrant).
- [ ] Backup/restauración acordados (PDFs + vectores cuestan regenerar).
- [ ] Conexión probada desde dev (`psql` o script Python) antes de Fase 5.

**Cierre:**

- [ ] Conexión MySQL read-only desde la máquina de desarrollo del agente.
- [ ] `docs/schema.sql` commiteado en `agent_femturisme` (DDL MySQL, sin datos).
- [ ] **PostgreSQL agent** accesible en staging; credenciales en `.env.example`.
- [ ] Staging acordado con ops (host, puerto, firewall hacia Python).

---

## 5. Fase 1 — Servicio Python en servidor {#fase-1}

**Objetivo:** agente Python ejecutándose en servidor con conectividad a **MySQL (catálogo)** y **PostgreSQL (agent)**, y endpoint HTTP operativo.

| # | Tarea | Detalle |
|---|-------|---------|
| 1.1 | Empaquetado | Docker Compose o imagen; `requirements.txt` |
| 1.2 | Despliegue staging | Contenedor/proceso en servidor accesible desde red interna |
| 1.3 | Configuración | `AGENT_*`, `MYSQL_*`, `POSTGRES_*`, `VECTOR_*` |
| 1.4 | Health check | `GET /health` o equivalente |
| 1.5 | Endpoints API | `POST /api/chat`, `POST /api/session/reset` (SSE) |
| 1.6 | Static files | Servir `app/static/chat/` (widget reutilizable) y preparar `app/static/admin/` (Fase 5) |
| 1.7 | Prueba conexión MySQL | Script que valida pool read-only desde el servicio |
| 1.8 | Prueba conexión PostgreSQL | Script que valida conexión a BD agent (Fase 0) |
| 1.9 | Smoke test agente | Pregunta de prueba; respuesta SSE (tools aún pueden ser stub parcial) |

**Cierre:**

- [ ] Servicio accesible en staging (IP/puerto interno o URL).
- [ ] MySQL alcanzable desde el contenedor/proceso.
- [ ] PostgreSQL agent alcanzable desde el contenedor/proceso.
- [ ] `/api/chat` responde.

---

## 6. Fase 2 — Exploración MySQL y diseño de queries {#fase-2}

**Guía detallada para el developer:** [fase-2-tools-mysql-ca.md](./fase-2-tools-mysql-ca.md).  
**Plantilla entregable:** [sql-mapeo.md](./sql-mapeo.md).

**Objetivo:** entender el schema legacy y diseñar, **por cada tool de catálogo**, la SQL parametrizada que el backend ejecutará cuando el LLM invoque esa tool.

### ¿Por qué queries predefinidas y no SQL generado al vuelo por el LLM?

Es una duda habitual entre programadores: *«Si le digo a Claude qué quiero, ¿por qué no escribe el `SELECT` y lo ejecuta? ¿No nos ahorraría mucha complejidad?»*

**Respuesta corta:** sí es **técnicamente posible**; es una **decisión de arquitectura**, no una limitación del LLM. El LLM **sí decide qué buscar** (tool + parámetros); el backend **no le deja escribir SQL libre** contra MySQL en producción.

**Flujo adoptado:**

```
Usuario: "Experiencias familiares en el Berguedà este fin de semana"
    │
    ▼
LLM elige tool + argumentos (visible en el SCHEMA):
    search_experiences(destination="Berguedà", category="Familiar")
    │
    ▼
Backend Python (execute()):
    • Valida parámetros
    • Ejecuta SQL fija + placeholders (:destination, :category)
    • LIMIT 20, solo tablas permitidas
    • Normaliza filas → JSON Anexo B
    │
    ▼
LLM redacta respuesta al usuario con las cards recibidas
```

El LLM **no ve** el SQL ni el schema MySQL. Solo ve el **SCHEMA de la tool** (nombre, descripción, parámetros permitidos) y el **JSON de resultados**.

**Argumentos resumidos** (tabla comparativa, riesgos de read-only, alternativas híbridas y decisión formal): **[Anexo D — Tools parametrizadas vs text-to-SQL](#anexo-d)**.

**Qué documenta `sql-mapeo.md`:** especificación para programadores (tablas, SQL parametrizada, mapeo JSON, reglas de negocio, casos de prueba). La SQL vive en `app/db/repositories/*.py`; el LLM no la lee. Ver también [Anexo D](#anexo-d).

### Tools de catálogo

| Tool | Dominio |
|------|---------|
| `search_experiences` | Ofertas, actividades, experiencias |
| `search_accommodations` | Allotjaments |
| `search_events` | Agenda, events |
| `search_routes` | Rutes |

### Metodología por tool

```
A. Explorar schema
   • Tablas de contenido, relaciones, ubicación, categorías, fechas, imágenes, slugs.
   • Diagrama ER parcial en sql-mapeo.md.

B. Definir necesidades del LLM
   • Parámetros SCHEMA: destination, category/type, date_from/date_to.
   • Campos JSON de salida (Anexo B) + extras: precio, coords, fechas exactas…
   • Reglas: publicado, vigente, orden, LIMIT.

C. Escribir query parametrizada
   • JOINs, WHERE, ORDER BY, LIMIT.
   • Sin concatenación de strings; placeholders.

D. Validar en MySQL
   • 3–5 casos reales (Berguedà + Familiar, Girona + hotel, agenda fin de semana…).
   • URLs canónicas construibles desde slug/id.

E. Documentar en sql-mapeo.md
```

### Entregable: `docs/sql-mapeo.md`

Por cada tool:

1. Tablas y relaciones.
2. Query SQL final.
3. Mapeo columna → campo JSON.
4. Reglas de negocio.
5. Casos de prueba (parámetros + resultado esperado).

### Herramientas

- DBeaver / MySQL Workbench + `schema.sql`
- Repo PHP (solo si aclara JOINs no obvios)
- General log MySQL en staging (último recurso)

**Cierre:**

- [ ] 4 tools con query documentada y probada en MySQL.
- [ ] SCHEMA de tools revisado si hace falta ampliar parámetros o descripciones.

---

## 7. Fase 3 — Tools de catálogo con MySQL {#fase-3}

**Guía detallada para el developer:** [fase-3-tools-mysql-ca.md](./fase-3-tools-mysql-ca.md) (pasos, archivos, ejemplos de código, cómo probar).

**Objetivo:** implementar capa de datos; cada `execute()` delega en un repositorio SQL.

| # | Tarea | Detalle |
|---|-------|---------|
| 3.1 | `app/db/connection.py` | Pool, timeout, read-only |
| 3.2 | Repositorios | `ExperiencesRepository`, `AccommodationsRepository`, `EventsRepository`, `RoutesRepository` |
| 3.3 | Implementar queries | Según `sql-mapeo.md` |
| 3.4 | Normalizador | `row → dict` según Anexo B |
| 3.5 | Refactor `execute()` | Cada tool llama a su repo |
| 3.6 | Tests | Casos de `sql-mapeo.md` automatizados en `tests/sql/` |
| 3.7 | Integración agente | Chat de prueba vía `/api/chat` con LLM real |

**Cierre:**

- [ ] Las 4 tools devuelven JSON desde MySQL en staging.
- [ ] Tests SQL pasan.
- [ ] Respuestas del agente coherentes en pruebas manuales.

---

## 8. Fase 4 — Widget en femturisme.cat {#fase-4}

**Objetivo:** globo flotante en todas las páginas; panel chat overlay; mismo dominio.

| # | Tarea | Detalle |
|---|-------|---------|
| 4.1 | Widget JS/CSS | Globo fijo bottom-right; panel abrir/cerrar; reutilizar lógica SSE existente |
| 4.2 | Include PHP | Footer/layout global |
| 4.3 | Reverse proxy | `/api/chat`, `/api/session/reset` → servicio Python |
| 4.4 | Estilo | Alineado con femturisme.cat |
| 4.5 | `page_context` | Enviar `{ section, ubicacio, municipality }` desde PHP/URL |
| 4.6 | Pruebas | Desktop, móvil, SSE estable |
| 4.7 | Producción | Rollout progresivo si aplica |

**Cierre:**

- [ ] Globo visible; click abre chat.
- [ ] Conversación funcional contra agente con MySQL.
- [ ] Sin errores CORS (same-origin).

---

## 9. Fase 5 — Ingesta de PDFs y vector store {#fase-5}

**Objetivo:** permitir al equipo femturisme **subir PDFs de guías municipales**, procesarlos automáticamente (extracción → chunks → embeddings) y **saber en todo momento** qué documentos hay, en qué estado están y si la indexación ha ido bien.

### Dónde se sube y quién lo hace

Los PDFs **no se suben desde femturisme.cat** ni desde el widget de chat. El chat solo **consulta** guías ya indexadas.

| Pregunta | Respuesta v1 |
|----------|--------------|
| **¿Desde dónde se sube?** | **Panel de administración** en el servicio Python del agente: `https://<host-agent>/admin/guides` (red interna, VPN o acceso restringido por IP + login). |
| **¿Quién lo usa?** | Personal femturisme / equipo técnico autorizado (no usuarios finales de la web). |
| **Alternativa para devs** | CLI: `python scripts/ingest_pdf.py --file … --municipality …` (mismo pipeline que la UI). |
| **¿Dónde se guarda el PDF original?** | Disco del servidor agent: `data/guides/{doc_id}/original.pdf` (o bucket S3-compatible si se acuerda con ops). |
| **¿Dónde se guarda el estado?** | **BD propia del agente** (PostgreSQL recomendado si se usa pgvector; no la MySQL read-only de femturisme). |

### Frontend admin en el servicio Python (aclaración)

Sí: el servicio Python tendrá un **frontend pequeño e interno**, separado de la web pública. Esto **no salía explícito** en el diagrama inicial; se concreta aquí.

| Pregunta | Respuesta |
|----------|-----------|
| **¿Python tendrá frontend?** | **Sí, pero solo de administración interna** (subir PDFs, listar documentos, ver status, reindexar). No es una segunda web pública. |
| **¿Qué NO incluye este frontend?** | No sustituye femturisme.cat. No edita contenido MySQL, no gestiona usuarios del CMS PHP, no es el chat del visitante. |
| **¿Cómo se implementa v1?** | Flask sirve HTML + JS/CSS desde `app/static/admin/` (páginas sencillas: lista, formulario subida, detalle documento). Sin React ni framework pesado. |
| **¿Quién accede?** | URL del host agent (`https://agent-intern.femturisme…/admin/guides`), protegida por login basic / token / VPN — **no indexada ni enlazada** desde la web pública. |
| **¿Por qué en Python y no en PHP?** | El pipeline ingest (extracción, embedding, vector store) vive en Python; poner el admin aquí evita duplicar lógica y APIs en el CMS legacy. |
| **¿Alternativa sin UI?** | **CLI** (`scripts/ingest_pdf.py`) para v1 técnico; el panel web puede posponerse si el equipo prefiere operar por terminal. |
| **Alternativa futura** | Panel dentro del backoffice PHP de femturisme que llama a la API admin del Python — posible post-v1, pero **no es el plan v1**. |

**Componentes del frontend admin (v1):**

| Pantalla | Ruta | Función |
|----------|------|---------|
| Lista de guías | `GET /admin/guides` | Tabla con todos los PDFs y status |
| Subir guía | `GET /admin/guides/upload` | Formulario: archivo + municipio + título |
| Detalle documento | `GET /admin/guides/{doc_id}` | Contadores, error, botones Reindexar / Probar búsqueda |

El **widget de chat** que ve el visitante sigue siendo JS servido desde Python (o copiado al PHP en Fase 4) e incrustado en femturisme.cat — es otro frontend con otro propósito.

```
┌─────────────────────────────────────────────────────────────────────┐
│ Equipo femturisme (navegador interno / VPN)                         │
│  Panel /admin/guides  →  subir PDF + municipio + título             │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ POST /admin/api/guides/upload
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Servicio agente Python                                              │
│  1. Guarda PDF en data/guides/{doc_id}/                             │
│  2. Registra documento en guide_documents (status: pending)         │
│  3. Pipeline ingest (extracción → chunks → embeddings → vector store)│
│  4. Actualiza status → indexed | failed                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ BD agent (guide_documents) │   │ Vector store              │
│ estado, contadores, errores│   │ chunks + embeddings       │
└───────────────────────────┘   └───────────────────────────┘
```

### Flujo de ingesta (paso a paso)

| Paso | Qué ocurre | Dónde se ve |
|------|------------|-------------|
| **1. Subida** | El operador selecciona PDF, municipio y título; el backend genera `doc_id` (UUID). | Panel admin: fila nueva con status `pending`. |
| **2. Extracción** | `pymupdf` / `pdfplumber` lee texto por página; se cuenta `pages_count`. | Status → `extracting`. |
| **3. Chunking** | Se divide en fragmentos de 500–1000 tokens con overlap 10–15%; se crea `chunks_count`. | Status → `chunking`. |
| **4. Embeddings** | Cada chunk pasa al modelo de embedding (batch); se guarda vector + metadatos en vector store. | Status → `embedding`; contador `embedded_chunks_count` sube. |
| **5. Indexación completa** | Cuando `embedded_chunks_count == chunks_count`, status → `indexed` y `indexed_at` = ahora. | Panel admin: badge verde **Indexado**. |
| **6. Error** | Cualquier paso puede fallar (PDF vacío, API embedding, vector store). | Status → `failed` + `error_message` visible en panel. |

**Reemplazar un PDF:** se sube nueva versión o se pulsa «Reindexar» en el panel. El pipeline **borra chunks antiguos** de ese `doc_id` en el vector store e indexa de nuevo (`version` incrementa).

### Cómo sabemos qué PDFs están subidos

Tres lugares complementarios:

| Dónde mirar | Qué muestra |
|-------------|-------------|
| **Panel `/admin/guides`** | Lista de todos los documentos: título, municipio, nombre archivo, **status**, páginas, chunks, modelo embedding. |
| **API `GET /admin/api/guides`** | Mismo listado en JSON (para scripts o monitorización). |
| **CLI `python scripts/ingest_pdf.py --list`** | Listado rápido desde terminal (dev/staging). |

**Tabla de registro** `guide_documents` (BD agent):

| Campo | Ejemplo | Uso |
|-------|---------|-----|
| `doc_id` | `a1b2-…` | Identificador único |
| `title` | `Guia turística Berga 2024` | Nombre visible en panel |
| `municipality` | `Berga` | Filtro RAG por municipio |
| `source_filename` | `guia_berga.pdf` | Nombre original del archivo |
| `storage_path` | `data/guides/a1b2…/original.pdf` | Dónde está el PDF |
| `status` | `indexed` | Estado del pipeline (ver tabla siguiente) |
| `error_message` | `Embedding API timeout` | Si `failed`, motivo |
| `pages_count` | `48` | Páginas extraídas |
| `chunks_count` | `120` | Fragmentos generados |
| `embedded_chunks_count` | `120` | Vectores creados (debe coincidir) |
| `embedding_model` | `text-embedding-3-small` | Modelo usado |
| `indexed_at` | `2026-06-23T10:00:00Z` | Cuándo terminó OK |
| `version` | `2` | Reindexaciones |

**Valores de `status`:**

| Status | Significado |
|--------|-------------|
| `pending` | Subido; pipeline aún no ha empezado |
| `extracting` | Leyendo texto del PDF |
| `chunking` | Dividiendo en fragmentos |
| `embedding` | Generando vectores (puede tardar minutos en PDFs grandes) |
| `indexed` | **Todo correcto** — disponible para chat RAG |
| `failed` | Error; revisar `error_message` y reintentar |

### Cómo se hacen los embeddings

1. **Modelo** — acordado en Fase 5 (p. ej. OpenAI `text-embedding-3-small` o modelo local). Se guarda en `embedding_model` para trazabilidad.
2. **Cuándo** — automáticamente tras la subida (job en background en v1; opcional cola Redis/Celery si hay muchos PDFs).
3. **Cómo** — por cada chunk de texto:
   - Se llama a la API de embedding (batch de 50–100 chunks para reducir coste).
   - Se hace **upsert** en el vector store con metadatos (ver JSON abajo).
4. **Dónde viven** — en el **vector store** (pgvector / Qdrant / Chroma), **no** en MySQL femturisme.
5. **Enlace documento ↔ vectores** — todos los chunks de un PDF comparten `doc_id`; la búsqueda RAG filtra por `municipality` + similitud vectorial.

**Metadatos mínimos por chunk** (en vector store):

```json
{
  "doc_id": "uuid",
  "doc_title": "Guia turística Berga 2024",
  "municipality": "Berga",
  "page": 12,
  "chunk_index": 3,
  "category": "restaurants",
  "source_file": "guia_berga.pdf",
  "embedding_model": "text-embedding-3-small",
  "indexed_at": "2026-06-23T10:00:00Z"
}
```

### Cómo sabemos si ha ido bien

**Criterios automáticos** (panel y BD lo reflejan):

| Comprobación | Condición de éxito |
|--------------|-------------------|
| Pipeline completado | `status == indexed` |
| Todos los chunks embeddados | `embedded_chunks_count == chunks_count` y `chunks_count > 0` |
| PDF no vacío | `pages_count > 0` |
| Sin error | `error_message IS NULL` |
| Fecha indexación | `indexed_at` informado |

**Pruebas manuales** (tras cada subida o antes de producción):

| Prueba | Cómo hacerla |
|--------|--------------|
| **Smoke test en panel** | Botón «Probar búsqueda» en el documento: query fija (p. ej. «restaurantes plaza mayor») → debe devolver chunks de ese `doc_id`. |
| **CLI verify** | `python scripts/ingest_pdf.py --verify {doc_id} --query "restaurantes Berga"` |
| **Prueba vía chat** | Pregunta al widget: «¿Dónde comer en Berga según la guía?» → respuesta debe citar `doc_title` y página (Fase 6). |
| **Logs** | Log estructurado por ingest: `doc_id`, paso, duración, chunks OK/KO. Alerta si `failed`. |

**Si falla:** el panel muestra `error_message`; el operador puede pulsar **Reindexar** (`POST /admin/api/guides/{doc_id}/reindex`) sin volver a subir el archivo.

### Tareas de implementación

| # | Tarea | Detalle |
|---|-------|---------|
| 5.1 | Elegir vector store + BD agent | pgvector (PostgreSQL) recomendado: metadatos + vectores juntos; alternativa Qdrant + PostgreSQL |
| 5.2 | Panel admin `/admin/guides` | UI mínima Flask (HTML + JS en `app/static/admin/`): lista, subida, detalle, reindexar, probar búsqueda |
| 5.3 | API admin | `POST /upload`, `GET /guides`, `GET /guides/{id}`, `POST /guides/{id}/reindex`, `POST /guides/{id}/smoke-test` |
| 5.4 | Tabla `guide_documents` | Schema anterior; migración al arrancar el servicio |
| 5.5 | Pipeline `app/rag/ingest.py` | Extracción → chunking → embedding → upsert; actualiza status en cada paso |
| 5.6 | CLI `scripts/ingest_pdf.py` | `--file`, `--list`, `--verify` para devs sin UI |
| 5.7 | Validación | ≥3 PDFs con `status=indexed`; smoke tests documentados |

**Cierre:**

- [ ] Panel admin accesible en staging (equipo femturisme puede subir un PDF de prueba).
- [ ] Se ve la lista de documentos con status y contadores (`pages`, `chunks`, `embedded`).
- [ ] ≥3 PDFs con `status=indexed` y smoke test OK en cada uno.
- [ ] Runbook: qué hacer si `failed` (revisar log, reindexar, contactar dev).

---

## 10. Fase 6 — Tool RAG (guías municipales) {#fase-6}

**Objetivo:** tool para conversaciones basadas en PDFs subidos.

| # | Tarea | Detalle |
|---|-------|---------|
| 6.1 | SCHEMA | `search_municipality_guides(query, municipality, category?)` |
| 6.2 | `execute()` | embed query → búsqueda vectorial filtrada por `municipality` → top-K (solo chunks de documentos con `status=indexed`) |
| 6.3 | Respuesta JSON | `{ query, municipality, total, results: [{ source, page, summary }] }` |
| 6.4 | Registrar en `ALL_TOOLS` | |
| 6.5 | Evaluación | ~20 preguntas: plaza mayor, aparcar, historia, transporte… |

**Ejemplos de uso:**

- "Estoy en la plaça Major de Berga, recomiéndame restaurantes cerca"
- "¿Dónde aparcar en el centro según la guía?"
- "Explícame la Patum según el folleto del municipio"

**Limitación v1:** sin GPS; precisión según texto del PDF y lugar que nombre el usuario.

**Cierre:**

- [ ] Tool operativa en staging con PDFs reales.
- [ ] Respuestas citan documento y página.

---

## 11. Fase 7 — Chat unificado {#fase-7}

**Objetivo:** un globo, un panel, catálogo MySQL + guías PDF sin que el usuario elija modo.

| # | Tarea | Detalle |
|---|-------|---------|
| 7.1 | `ALL_TOOLS` | 4 catálogo + guías RAG |
| 7.2 | System prompt | Cuándo catálogo, cuándo guías, cuándo ambos; idioma usuario |
| 7.3 | `page_context` | Hint de municipio/sección desde la página actual |
| 7.4 | Multi-tool | Permitir catálogo + guías en un mismo turno |
| 7.5 | Sugerencias UI | Contextuales según sección de la web |
| 7.6 | Pruebas | ~30 conversaciones (catálogo, guías, mixtas) |

**Routing v1 (recomendado):** LLM elige tools vía schemas; sin router externo.

**Ejemplo mixto:**

> "Som a Berga, què puc fer avui i on dinar segons la guia?"

Tools: `search_events` + `search_municipality_guides`.

**Cierre:**

- [ ] Un endpoint, un widget.
- [ ] Routing correcto en ≥80% casos de prueba acordados.

---

## 12. Fase 8 — Producción y operaciones {#fase-8}

| # | Tarea |
|---|-------|
| 8.1 | Rate limiting en `/api/chat` |
| 8.2 | Logs: tool_calls, latencia SQL, latencia vector, LLM |
| 8.3 | Alertas: BD, vector store, API keys, error rate |
| 8.4 | Historial sesión persistente (Redis/DB) si multi-instancia |
| 8.5 | Streaming LLM nativo (opcional) |
| 8.6 | Runbooks | BD caída, query lenta, ingest PDF `failed`, índice vector desactualizado |
| 8.7 | Documentación operativa para equipo femturisme |

---

## 13. Criterios de éxito

| Área | Criterio |
|------|----------|
| **Integración web** | Globo en femturisme.cat; chat same-origin |
| **Catálogo** | 4 tools MySQL; datos útiles para el LLM |
| **Guías** | PDFs indexados; respuestas con fuente |
| **Chat único** | Usuario no distingue orígenes de datos |
| **Ops** | Despliegue reproducible; credenciales segregadas |

---

## 14. Riesgos y decisiones pendientes

| Riesgo | Mitigación |
|--------|------------|
| Schema MySQL legacy opaco | Exploración Fase 2; apoyo mantenedor PHP; general log |
| Queries lentas | EXPLAIN; índices; LIMIT; caché futuro |
| PDFs sin detalle geográfico | Metadatos manuales; comunicar límite v1 |
| Coste LLM + embeddings | Modelos ligeros; límites por sesión |
| Desfase datos web vs agente | Misma BD; reglas de negocio explícitas en SQL |

**Decisiones pendientes:**

- [x] Catálogo MySQL: tools parametrizadas vs text-to-SQL → **tools parametrizadas en v1** ([Anexo D](#anexo-d))
- [ ] Vector store: pgvector (misma PostgreSQL) vs Qdrant + PostgreSQL → decidir en **Fase 0** (tarea 0.9)
- [ ] Hosting Python: misma máquina que PHP vs dedicado
- [ ] Flask vs migración FastAPI
- [ ] Persistencia historial chat en v1
- [ ] Modelo embedding y LLM producción

---

## 15. Anexo A — Checklist SQL por tool

Completar en **Fase 2** antes de implementar en **Fase 3**.

| # | Checklist |
|---|-----------|
| C1 | Tablas y JOINs identificados |
| C2 | Filtro `destination` mapeado |
| C3 | Filtros opcionales (tipo, categoría, fechas) mapeados |
| C4 | Reglas de negocio (publicado, vigente, orden) |
| C5 | Campos JSON definidos (Anexo B + extras) |
| C6 | Query en `sql-mapeo.md` |
| C7 | 3–5 casos probados en MySQL |
| C8 | URLs de resultados correctas |

**Parámetros por tool:**

| Tool | Parámetros SCHEMA |
|------|-------------------|
| `search_experiences` | `destination`, `category?` |
| `search_accommodations` | `destination`, `type?` |
| `search_events` | `destination`, `date_from?`, `date_to?` |
| `search_routes` | `destination`, `type?` |

---

## 16. Anexo B — Contrato JSON hacia el LLM

### Card de catálogo

```json
{
  "id": "string | null",
  "type": "string | null",
  "title": "string",
  "location": "string | null",
  "description": "string | null",
  "url": "string | null",
  "image": "string | null",
  "date": "string | null"
}
```

### Wrapper (ej. experiences)

```json
{
  "destination": "string",
  "category": "string | null",
  "total": "number | null",
  "results": [],
  "error": "string | null"
}
```

### Resultado RAG (guías)

```json
{
  "query": "string",
  "municipality": "string",
  "total": "number",
  "results": [
    {
      "source": "string",
      "page": "number | null",
      "summary": "string",
      "doc_id": "string | null"
    }
  ]
}
```

---

## 17. Anexo C — Estructura de carpetas

```
agent_femturisme/
├── app/
│   ├── admin/
│   │   └── guides_routes.py    ← panel /admin/guides (Fase 5)
│   ├── db/
│   │   ├── connection.py
│   │   └── repositories/
│   ├── rag/
│   │   ├── ingest.py           ← pipeline PDF → chunks → embeddings
│   │   ├── embedder.py
│   │   ├── vector_store.py
│   │   └── municipality_guides.py
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── llm_service.py
│   │   └── tools/
│   └── static/
│       ├── chat/
│       │   ├── widget.js
│       │   └── widget.css
│       └── admin/              ← UI listado y subida PDFs
├── data/
│   └── guides/                 ← PDFs originales por doc_id
├── docs/
│   ├── agente.md
│   ├── plan-integracion.md
│   └── sql-mapeo.md          ← Fase 2
├── scripts/
│   ├── test_sql_queries.py
│   └── ingest_pdf.py
└── tests/
    ├── sql/
    └── rag/
```

---

## 18. Anexo D — Tools parametrizadas vs text-to-SQL {#anexo-d}

Documento de decisión arquitectónica para el equipo de desarrollo. Responde: *¿por qué el backend no deja al LLM escribir SQL libre contra MySQL? ¿No simplificaría el agente?*

### D.1 La pregunta

En un chat con tool use, el LLM puede recibir una tool genérica:

```json
{
  "name": "execute_sql",
  "parameters": {
    "query": "SELECT titol, slug FROM experiencies WHERE ..."
  }
}
```

El backend ejecutaría esa cadena contra MySQL y devolvería las filas al LLM. **Eso es posible.** Muchos prototipos y demos de «agente + base de datos» funcionan exactamente así.

La pregunta relevante no es «¿se puede?» sino «¿qué complejidad eliminamos y qué complejidad movemos a otro sitio?».

### D.2 Dos arquitecturas comparadas

#### A) Tools parametrizadas (decisión de este plan)

```
Usuario (NL) → LLM elige tool + params → Python ejecuta SQL fija → JSON normalizado → LLM responde
```

- El LLM ve: **SCHEMA de 4–5 tools** (nombre, descripción, parámetros).
- El LLM **no ve**: schema MySQL, nombres de tablas, SQL.
- El backend controla: tablas, JOINs, reglas de negocio, `LIMIT`, formato de salida.

#### B) Text-to-SQL al vuelo (alternativa descartada para v1)

```
Usuario (NL) → LLM genera SELECT → Python ejecuta tal cual → filas crudas → LLM responde
```

- El LLM ve: **schema completo** (o un resumen) + instrucciones de generar SQL.
- El LLM **escribe**: la query en cada turno.
- El backend debe: validar, restringir, limitar, normalizar — o confiar ciegamente.

### D.3 Qué parece ahorrar text-to-SQL

| Lo que no haría falta (en principio) | Detalle |
|--------------------------------------|---------|
| 4 repositorios Python | Una sola tool `execute_sql` |
| `sql-mapeo.md` por tool | El LLM «descubre» tablas al vuelo |
| Ampliar parámetros SCHEMA | Cualquier filtro sería SQL ad hoc |
| Fase 2–3 larga | MVP más rápido para probar conexión BD |

Para un **experimento interno** o una **demo**, esto puede ser cierto.

### D.4 Qué complejidad no desaparece (solo cambia de sitio)

Montar text-to-SQL en **producción** frente a usuarios reales exige capas que, con tools parametrizadas, ya están resueltas en código:

| Capa | Tools parametrizadas | Text-to-SQL en producción |
|------|----------------------|---------------------------|
| Conocer el schema | Lo estudia el dev en Fase 2 | Hay que **inyectar el schema al LLM** en cada turno (miles de tokens) o resumirlo mal |
| Reglas de negocio (`publicado = 1`, fechas vigentes, idioma…) | Van en la SQL fija del repo | El LLM debe **inferirlas** o las omite |
| Límite de filas | `LIMIT 20` en código | Validador que **rechace o reescriba** queries sin `LIMIT` |
| Tablas permitidas | Solo las del repositorio | Parser + allowlist: **solo `SELECT`**, solo tablas X/Y/Z |
| Formato al chat | JSON estable ([Anexo B](#16-anexo-b--contrato-json-hacia-el-llm)) | Normalizador post-query: filas → cards con `title`, `url`, `image` |
| Tests automatizados | Casos fijos en CI (`destination=Berguedà` → N filas) | La SQL **cambia cada turno** y con cada versión del modelo |
| Depuración | «La query de experiences filtra mal el JOIN X» | «Claude generó otra SQL distinta ayer que funcionaba» |
| Coste/latencia LLM | Prompt pequeño (solo SCHEMA de tools) | Schema grande + SQL generada + reintentos si falla |

**Conclusión:** no eliminas la Fase 2; la conviertes en «meter todo el schema legacy en el prompt y confiar en que el modelo lo interprete bien en cada pregunta».

### D.5 Por qué MySQL read-only no resuelve el problema

El usuario `agent_read` sin permisos de escritura **evita borrar o modificar datos**, pero **no limita qué se puede leer** ni **cuánto cuesta leerlo**.

Ejemplos de queries que un LLM puede generar sin mala intención:

```sql
-- Tablas sensibles (si existen y el usuario tiene SELECT)
SELECT email, password_hash FROM users LIMIT 1000;

-- Cartesian product / query costosa
SELECT * FROM orders o
JOIN order_items i ON ...
JOIN products p ON ...
JOIN categories c ON ...;

-- Columnas inventadas (error en runtime)
SELECT titulo, allows_dogs FROM experiencies WHERE zona = 'Berguedà';
-- → Unknown column 'allows_dogs'
```

Los fallos habituales no son ataques; son **alucinaciones de columnas**, **JOINs incorrectos** y **olvidar filtros de negocio** en schemas legacy con nombres crípticos (`tbl_cnt`, `rel_ubicacio_2`, etc.).

### D.6 El problema concreto de femturisme

Hay tres capas que el agente debe acertar a la vez:

| Capa | Contenido | Con text-to-SQL |
|------|-----------|-----------------|
| **1. Schema legacy** | Tablas, relaciones, nombres no obvios | El LLM debe acertar JOINs en cada turno |
| **2. Reglas de negocio** | Publicado, vigente, idioma — a menudo en PHP, no en FK | El LLM no las conoce salvo que estén documentadas en el prompt |
| **3. Contrato de producto** | Cards con URL canónica, imagen, título ([Anexo B](#16-anexo-b--contrato-json-hacia-el-llm)) | Las filas SQL crudas no coinciden con lo que el chat debe mostrar |

Con **tools parametrizadas**, el LLM solo resuelve la capa de **intención** («qué buscar»). Las capas 1–3 las garantiza el backend en código revisado.

### D.7 Qué flexibilidad sí aporta el LLM (sin SQL libre)

El LLM ya aporta la flexibilidad que el usuario percibe:

| Capacidad | Ejemplo |
|-----------|---------|
| Elegir tool(s) | Agenda + guía PDF en la misma pregunta |
| Inferir parámetros | «Berguedà en familia» → `destination`, `category` |
| Criterios blandos | «Con perros» → filtra sobre `description` del JSON |
| Combinar resultados | Mezcla catálogo MySQL + chunks RAG en la respuesta |
| Idioma y tono | Responde en catalán/castellano según el usuario |

Esa flexibilidad **no requiere** que el LLM escriba SQL.

### D.8 Comparación de esfuerzo total (v1, 4 dominios de catálogo)

| Dimensión | Tools parametrizadas | Text-to-SQL al vuelo |
|-----------|----------------------|----------------------|
| Complejidad upfront | Alta (Fase 2–3, una vez) | Baja (tool genérica rápida) |
| Complejidad ongoing | Baja (cambios en PR) | Alta (validadores, prompt schema, debugging) |
| Riesgo en producción | Bajo | Medio–alto |
| Predecibilidad | Alta | Baja |
| Testabilidad en CI | Alta | Baja |
| Superficie de datos expuesta | Mínima (tablas de catálogo) | Toda tabla con `SELECT` permitido |

Para **cuatro dominios acotados** (ofertas, allotjaments, agenda, rutes), parametrizar suele implicar **menos trabajo total** que montar un sandbox SQL robusto.

### D.9 Qué habría que implementar igual con text-to-SQL

Si se eligiera text-to-SQL para producción, el backend necesitaría como mínimo:

1. **Inyección de schema** — `docs/schema.sql` o subconjunto en cada request (coste tokens).
2. **Parser SQL** — rechazar `INSERT`, `UPDATE`, `DELETE`, `DROP`, subqueries peligrosas, múltiples statements.
3. **Allowlist de tablas** — solo tablas de catálogo; rechazar el resto.
4. **`LIMIT` obligatorio** — inyectar o rechazar si falta (p. ej. máx. 50 filas).
5. **Timeout de query** — p. ej. 2 s; matar queries lentas.
6. **Normalizador de salida** — filas → JSON Anexo B (URLs, imágenes, slugs).
7. **Logging de queries generadas** — para auditar qué ejecutó el LLM.
8. **Reintentos** — cuando la SQL falla por columna inexistente (común).

Eso es comparable en esfuerzo a implementar 4 repositorios, pero **más frágil** en runtime.

### D.10 Alternativas intermedias

| Alternativa | Descripción | Cuándo tiene sentido |
|-------------|-------------|----------------------|
| **Vistas SQL en MySQL** | `CREATE VIEW v_experiences_public AS …`; el LLM solo consulta vistas | Reduce tablas sensibles; no elimina alucinaciones ni JSON inestable |
| **Text-to-SQL solo en staging** | Tool interna para devs que exploran el schema | Fase 2 de exploración; no tráfico de usuarios |
| **Hybrid post-v1** | Tools parametrizadas + quinta tool muy restringida para casos raros | Solo si aparece demanda real no cubierta por las 4 tools |
| **Schema-on-read en prompt** | Resumen manual de 20 tablas clave en system prompt | Compromiso frágil; requiere mantenimiento manual |

### D.11 Decisión formal (v1)

| Aspecto | Decisión |
|---------|----------|
| **Mecanismo catálogo** | Tools parametrizadas: `search_experiences`, `search_accommodations`, `search_events`, `search_routes` |
| **SQL** | Fija en `app/db/repositories/*.py`; documentada en `sql-mapeo.md` |
| **Visibilidad LLM** | SCHEMA de tools + JSON de resultados; **sin** schema MySQL ni SQL |
| **Text-to-SQL** | **No** en el chat de producción v1 |
| **Revisión** | Tras v1 en producción, si >20% de preguntas de catálogo no se resuelven con las 4 tools, evaluar ampliar parámetros o vistas SQL antes que text-to-SQL |

### D.12 Respuesta lista para compartir con el cliente

> «¿Por qué no dejamos que Claude escriba la query?»
>
> Porque **sí se puede**, pero **no reduce la complejidad total** en un entorno de producción con schema legacy: desplaza el trabajo de «escribir cuatro queries bien hechas» a «validar SQL arbitraria, inyectar schema, normalizar resultados y depurar queries rotas en cada conversación». Para un catálogo turístico con respuestas en cards y datos sensibles en la misma BD, las tools parametrizadas ofrecen **menos sorpresas**, **tests reproducibles** y **menor superficie de exposición de datos». El LLM sigue siendo flexible en *qué* buscar y *cómo* responder; lo que fijamos en código es *cómo* acceder a MySQL de forma segura y estable.

---

## Próximo paso

1. **[Fase 0](#fase-0)** — credenciales MySQL read-only + PostgreSQL agent en staging + commitear `docs/schema.sql`.
2. **[Fase 1](#fase-1)** — desplegar servicio Python en staging con conexión MySQL.
3. **[Fase 2](#fase-2)** — primera query documentada en `sql-mapeo.md` para `search_experiences`.
