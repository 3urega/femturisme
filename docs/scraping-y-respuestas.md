# Scraping, endpoints y construcción de respuestas

Documento de referencia completo. Complementa [agente.md](./agente.md) con el detalle de **cómo una página HTML de femturisme.cat se convierte en la respuesta del chat**, todos los endpoints que usa el agente, parámetros, formatos JSON y ejemplos reproducibles.

---

## Índice

1. [Pipeline completo: HTML → JSON → respuesta](#1-pipeline-completo-html--json--respuesta)
2. [Qué ve el navegador vs qué ve el LLM](#2-qué-ve-el-navegador-vs-qué-ve-el-llm)
3. [Capa de scraping (`scraper.py`)](#3-capa-de-scraping-scraperpy)
4. [Contrato LLM (SCHEMA) vs implementación (`execute`)](#4-contrato-llm-schema-vs-implementación-execute)
5. [Referencia de endpoints femturisme.cat](#5-referencia-de-endpoints-femturismecat)
6. [Tool: `search_experiences`](#6-tool-search_experiences)
7. [Tool: `search_accommodations`](#7-tool-search_accommodations)
8. [Tool: `search_events`](#8-tool-search_events)
9. [Tool: `search_routes`](#9-tool-search_routes)
10. [Tool: `search_local_knowledge`](#10-tool-search_local_knowledge)
11. [Ejemplo extremo a extremo (Berguedà en familia)](#11-ejemplo-extremo-a-extremo-berguedà-en-familia)
12. [Más ejemplos por tipo de pregunta](#12-más-ejemplos-por-tipo-de-pregunta)
13. [Errores y límites](#13-errores-y-límites)
14. [Qué NO está implementado](#14-qué-no-está-implementado)
15. [Archivos de código](#15-archivos-de-código)

---

## 1. Pipeline completo: HTML → JSON → respuesta

Cuando el usuario escribe en el chat, ocurren **dos llamadas al LLM** si hace falta una herramienta (más si hay varias iteraciones de tools).

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ITERACIÓN 1 — Decisión                                                   │
│                                                                          │
│  Usuario: "Voy al Berguedà con familia este fin de semana"               │
│       ↓                                                                  │
│  LLM + schemas de 5 tools → elige search_experiences, search_events      │
│       ↓                                                                  │
│  Backend: execute() × N                                                  │
│       ↓                                                                  │
│  GET femturisme.cat → HTML completo                                      │
│       ↓                                                                  │
│  BeautifulSoup + extract_cards() → JSON (máx. 6 tarjetas por tool)       │
│       ↓                                                                  │
│  Historial += tool_use (assistant) + tool_result (user)                  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ ITERACIÓN 2 — Síntesis                                                   │
│                                                                          │
│  LLM recibe: pregunta original + JSON de resultados                      │
│       ↓                                                                  │
│  Redacta respuesta en lenguaje natural (catalán/castellano/inglés)       │
│       ↓                                                                  │
│  AgentService emite text_chunk + done por SSE → UI                       │
└──────────────────────────────────────────────────────────────────────────┘
```

**Punto crítico:** el LLM **nunca recibe HTML**. Solo recibe:
- La pregunta del usuario.
- Los schemas de tools (en la iteración 1).
- El JSON devuelto por `execute()` (en la iteración 2).

El HTML lo procesa exclusivamente Python (`requests` + BeautifulSoup) en el backend.

### Código que conecta scraping → LLM

En `app/services/agent_service.py`:

```python
raw_result = execute_tool(tc.name, tc.input)   # JSON string desde execute()

tool_results_content.append({
    'type':        'tool_result',
    'tool_use_id': tc.id,
    'content':     raw_result,                 # el LLM lee esto en la siguiente iteración
})

history.append({'role': 'user', 'content': tool_results_content})
# → siguiente llm.chat(messages=history, tools=ALL_TOOLS)
```

---

## 2. Qué ve el navegador vs qué ve el LLM

### En el navegador (HTML)

Al abrir:

`https://www.femturisme.cat/ofertes?ubicacio=Berguedà&tipus=Familiar`

ves una página completa: menú, filtros, footer, newsletter, sidebar de agenda, **y** un grid de tarjetas `.ft-card`.

### En el backend (tras scraping)

El scraper **descarta** nav, footer, CSS, scripts y la mayoría del DOM. Solo extrae nodos `a.ft-card` del listado principal.

### En el LLM (JSON)

Como mucho **6 objetos** por tool, con campos acotados:

```json
{
  "destination": "Berguedà",
  "category": "Familiar",
  "total": "Berguedà (Comarca) · 19 resultats",
  "results": [
    {
      "id": "…",
      "type": "…",
      "title": "Pack Familiar (Muntanya de Sal i Castell de Cardona)",
      "location": "Cardona",
      "description": "Pack d'un dia de visites teatralitzades…",
      "url": "/ofertes/…",
      "image": "https://…"
    }
  ]
}
```

### Tabla: qué se conserva y qué se pierde

| En la web | En el agente | Notas |
|-----------|--------------|-------|
| Toda la página HTML | No | Solo tarjetas del listado |
| N resultados (p. ej. 19) | Máximo 6 en `results` | El resto no llega al LLM |
| Ficha detallada al hacer clic en una oferta | No | No hay scrape de `/ofertes/slug` |
| Precio, horarios, reserva | Solo si aparecen en `.ft-item-desc` del listado | Suele ser texto corto |
| Imagen | URL en campo `image` | La UI del chat no las muestra siempre |
| Contador total | Campo `total` (texto de `.ft-filter-bar__count`) | Informativo para el LLM |
| Fecha (en agenda) | Campo `date` | Post-procesado desde `.ft-card__loc` |

---

## 3. Capa de scraping (`scraper.py`)

**Archivo:** `app/services/tools/scraper.py`  
**Base URL:** `https://www.femturisme.cat`

### `fetch_page(path, params)`

| Aspecto | Valor |
|---------|-------|
| Método | `GET` |
| Headers | User-Agent Chrome, `Accept-Language: ca-ES` |
| Timeout | 15 segundos |
| Entrada | `path` (ej. `/ofertes`) + `params` dict |
| Salida | `BeautifulSoup` o `None` si falla la petición |

URL final: `BASE_URL + path + "?" + urlencode(params)`

### `extract_cards(soup, limit)`

| Selector CSS | Campo JSON | Descripción |
|--------------|------------|-------------|
| `a.ft-card` | (contenedor) | Cada tarjeta del listado |
| `data-el-id` | `id` | ID interno del elemento |
| `data-el-type` | `type` | Tipo de contenido |
| `.ft-card__title`, `h2`, `h3`, `h4` | `title` | Título |
| `.ft-card__loc` | `location` | Ubicación (en agenda → se renombra a `date`) |
| `.ft-item-desc`, `p` | `description` | Texto resumen |
| `href` | `url` | Ruta relativa a la ficha |
| `[data-wl-img]` o `.ft-card__media` style | `image` | URL de imagen |

Las tools pasan `limit=6` (el default del scraper es 8 si no se especifica).

### `result_count(soup)`

Lee el texto de `.ft-filter-bar__count`, p. ej. `"Berguedà (Comarca) · 19 resultats"`.

---

## 4. Contrato LLM (SCHEMA) vs implementación (`execute`)

Cada tool vive en `app/services/tools/<nombre>.py` con **dos piezas separadas**:

| Pieza | Quién la usa | Contiene |
|-------|--------------|----------|
| `SCHEMA` | LLM (vía `ALL_TOOLS`) | `name`, `description`, `input_schema` |
| `execute(tool_input)` | Backend Python | URL, query params, scraping, `json.dumps()` |

**El LLM no conoce** `/ofertes`, `ubicacio`, ni selectores CSS. Solo conoce parámetros como `destination` y `category`.

Registro central: `app/services/tools/__init__.py` → `ALL_TOOLS` + `_EXECUTORS`.

---

## 5. Referencia de endpoints femturisme.cat

Resumen de **todos los endpoints HTTP** que el agente puede atacar hoy:

| Tool | Método | Path | Query params (sitio) | Origen en tool |
|------|--------|------|----------------------|----------------|
| `search_experiences` | GET | `/ofertes` | `ubicacio`, `tipus` | `destination`, `category` |
| `search_accommodations` | GET | `/on-dormir` | `ubicacio`, `tipus` | `destination`, `type` |
| `search_events` | GET | `/agenda` | `ubicacio`, `data_inici`, `data_fi` | `destination`, `date_from`, `date_to` |
| `search_routes` | GET | `/rutes` | `ubicacio`, `tipus` | `destination`, `type` |
| `search_local_knowledge` | — | — | — | No hace HTTP (stub) |

**Parámetro común `ubicacio`:** texto libre (pueblo, comarca, región). El sitio resuelve la coincidencia. Ejemplos que funcionan en pruebas: `Berguedà`, `Girona`, `Costa Brava`, `Pirineu`, `Barcelona`.

---

## 6. Tool: `search_experiences`

**Archivo:** `app/services/tools/experiences.py`  
**Endpoint:** `GET https://www.femturisme.cat/ofertes`

### Parámetros de la tool (input del LLM)

| Parámetro | Obligatorio | Tipo | Descripción |
|-----------|-------------|------|-------------|
| `destination` | Sí | string | Localidad, comarca o zona |
| `category` | No | string | Filtro de tipo de oferta |

### Mapeo → query string

| Parámetro tool | Query param | Transformación |
|----------------|-------------|----------------|
| `destination` | `ubicacio` | Directo |
| `category` | `tipus` | `_CATEGORY_MAP` o valor tal cual |

### Valores de `category` / `tipus`

| Input LLM (ejemplos) | `tipus` enviado al sitio |
|----------------------|--------------------------|
| `familiar`, `family` | `Familiar` |
| `activitats`, `activities` | `Activitats` |
| `visites`, `guided` | `Visites guiades` |
| `escapades`, `escapes` | `Escapades` |
| `menus`, `gastronomy` | `Menús` |
| `Familiar` (exacto) | `Familiar` |

Valores documentados en schema: `Activitats`, `Allotjaments`, `Familiar`, `Visites guiades`, `Escapades`, `Menús`.

### JSON de respuesta

```json
{
  "destination": "string",
  "category": "string | null",
  "total": "string | null",
  "results": [ { "id", "type", "title", "location", "description", "url", "image" } ]
}
```

### URLs de prueba en el navegador

```
https://www.femturisme.cat/ofertes?ubicacio=Berguedà
https://www.femturisme.cat/ofertes?ubicacio=Berguedà&tipus=Familiar
https://www.femturisme.cat/ofertes?ubicacio=Costa+Brava&tipus=Visites+guiades
https://www.femturisme.cat/ofertes?ubicacio=Girona&tipus=Menús
```

### Ejemplo tool call → URL

```json
{ "destination": "Berguedà", "category": "Familiar" }
```

→ `GET /ofertes?ubicacio=Berguedà&tipus=Familiar`

---

## 7. Tool: `search_accommodations`

**Archivo:** `app/services/tools/accommodations.py`  
**Endpoint:** `GET https://www.femturisme.cat/on-dormir`

### Parámetros de la tool

| Parámetro | Obligatorio | Tipo | Descripción |
|-----------|-------------|------|-------------|
| `destination` | Sí | string | Localidad, comarca o zona |
| `type` | No | string | Tipo de alojamiento |

### Mapeo → query string

| Parámetro tool | Query param | Transformación |
|----------------|-------------|----------------|
| `destination` | `ubicacio` | Directo |
| `type` | `tipus` | Directo (sin mapeo) |

### Valores de `type` / `tipus`

Documentados en schema: `hotel`, `casa-rural`, `hostal`, `camping`, `apartament`.

Deben coincidir con los filtros del sitio (formato con guión en `casa-rural`).

### JSON de respuesta

```json
{
  "destination": "string",
  "type": "string | null",
  "total": "string | null",
  "results": [ { "id", "type", "title", "location", "description", "url", "image" } ]
}
```

### URLs de prueba

```
https://www.femturisme.cat/on-dormir?ubicacio=Pirineu
https://www.femturisme.cat/on-dormir?ubicacio=Pirineu&tipus=casa-rural
https://www.femturisme.cat/on-dormir?ubicacio=Girona&tipus=hotel
https://www.femturisme.cat/on-dormir?ubicacio=Costa+Brava&tipus=camping
```

### Ejemplo tool call → URL

```json
{ "destination": "Vall d'Aran", "type": "casa-rural" }
```

→ `GET /on-dormir?ubicacio=Vall+d'Aran&tipus=casa-rural`

---

## 8. Tool: `search_events`

**Archivo:** `app/services/tools/events.py`  
**Endpoint:** `GET https://www.femturisme.cat/agenda`

### Parámetros de la tool

| Parámetro | Obligatorio | Tipo | Descripción |
|-----------|-------------|------|-------------|
| `destination` | Sí | string | Localidad, comarca o zona |
| `date_from` | No | string | Fecha inicio `YYYY-MM-DD` |
| `date_to` | No | string | Fecha fin `YYYY-MM-DD` |

### Mapeo → query string

| Parámetro tool | Query param | Transformación |
|----------------|-------------|----------------|
| `destination` | `ubicacio` | Directo |
| `date_from` | `data_inici` | Directo |
| `date_to` | `data_fi` | Directo |

Las fechas las **calcula el LLM** a partir de expresiones como "este fin de semana" o "este mes". No hay lógica de fechas en el backend.

### Post-procesado específico de agenda

En el HTML, la fecha del evento aparece en `.ft-card__loc`. El backend la mueve:

```python
c['date']     = c.pop('location')
c['location'] = None
```

### JSON de respuesta

```json
{
  "destination": "string",
  "date_from": "YYYY-MM-DD | null",
  "date_to": "YYYY-MM-DD | null",
  "total": "string | null",
  "results": [
    {
      "id", "type", "title",
      "date": "23 de juny | Del 23 al 24 de juny",
      "location": null,
      "description", "url", "image"
    }
  ]
}
```

### URLs de prueba

```
https://www.femturisme.cat/agenda?ubicacio=Barcelona
https://www.femturisme.cat/agenda?ubicacio=Berguedà&data_inici=2026-06-27&data_fi=2026-06-29
https://www.femturisme.cat/agenda?ubicacio=Tarragona&data_inici=2026-07-01&data_fi=2026-07-31
```

### Ejemplo tool call → URL

```json
{
  "destination": "Berguedà",
  "date_from": "2026-06-27",
  "date_to": "2026-06-29"
}
```

→ `GET /agenda?ubicacio=Berguedà&data_inici=2026-06-27&data_fi=2026-06-29`

---

## 9. Tool: `search_routes`

**Archivo:** `app/services/tools/routes_tool.py`  
**Endpoint:** `GET https://www.femturisme.cat/rutes`

### Parámetros de la tool

| Parámetro | Obligatorio | Tipo | Descripción |
|-----------|-------------|------|-------------|
| `destination` | Sí | string | Localidad, comarca o zona |
| `type` | No | string | Tipo de ruta |

### Mapeo → query string

| Parámetro tool | Query param | Transformación |
|----------------|-------------|----------------|
| `destination` | `ubicacio` | Directo |
| `type` | `tipus` | `_TYPE_MAP` (lowercase) o valor tal cual |

### Valores de `type` / `tipus`

| Input LLM | `tipus` enviado |
|-----------|-----------------|
| `hiking`, `walking`, `peu` | `A peu` |
| `cycling`, `bike`, `bicicleta` | `En bicicleta` |
| `culture`, `cultural` | `Cultura` |
| `adventure`, `sport` | `Esports i aventura` |
| `gastro`, `food` | `Gastronomia` |
| `history`, `historia` | `Història` |
| `nature`, `natura` | `Natura` |
| `literary` | `Literària` |
| `A peu`, `Natura`, … (catalán exacto) | Sin cambio |

### JSON de respuesta

```json
{
  "destination": "string",
  "type": "string | null",
  "total": "string | null",
  "results": [ { "id", "type", "title", "location", "description", "url", "image" } ]
}
```

### URLs de prueba

```
https://www.femturisme.cat/rutes?ubicacio=Berguedà
https://www.femturisme.cat/rutes?ubicacio=Empordà&tipus=A+peu
https://www.femturisme.cat/rutes?ubicacio=Pirineu&tipus=Natura
https://www.femturisme.cat/rutes?ubicacio=Barcelona&tipus=Cultura
```

### Ejemplo tool call → URL

```json
{ "destination": "Empordà", "type": "bike" }
```

→ `GET /rutes?ubicacio=Empordà&tipus=En+bicicleta`

---

## 10. Tool: `search_local_knowledge`

**Archivo:** `app/services/tools/local_knowledge.py`  
**Endpoint:** ninguno (stub)

### Parámetros de la tool

| Parámetro | Obligatorio | Tipo | Descripción |
|-----------|-------------|------|-------------|
| `query` | Sí | string | Consulta semántica |
| `location` | No | string | Contexto geográfico (default: `"Berguedà"`) |

### Comportamiento actual

No hace HTTP. Devuelve siempre 5 chunks hardcodeados sobre Berga/Berguedà (aparcamiento, horarios oficina de turismo, transporte, restaurantes, historia).

### JSON de respuesta

```json
{
  "query": "string",
  "location": "string",
  "total": 5,
  "results": [
    {
      "source": "Guia Turística de Berga 2024 (PDF)",
      "page": 3,
      "summary": "Història de Berga: …"
    }
  ]
}
```

### Diseño futuro

Embedding de `query` + búsqueda en vector store (pgvector, Chroma, Pinecone…). Entonces sí sería un endpoint/corpus distinto al scraping de listados.

---

## 11. Ejemplo extremo a extremo (Berguedà en familia)

### Pregunta

> *"Voy al Berguedà con familia, recomiéndame algo para este fin de semana"*

### Paso A — Primera llamada LLM

**Entrada:** system prompt + mensaje usuario + schemas de 5 tools.

**Salida:** dos tool calls:

```json
[
  {
    "name": "search_experiences",
    "input": { "destination": "Berguedà", "category": "Familiar" }
  },
  {
    "name": "search_events",
    "input": {
      "destination": "Berguedà",
      "date_from": "2026-06-27",
      "date_to": "2026-06-29"
    }
  }
]
```

### Paso B — Scraping (backend)

**Request 1:**

```
GET https://www.femturisme.cat/ofertes?ubicacio=Berguedà&tipus=Familiar
```

HTML → 6 cards → JSON (fragmento):

```json
{
  "destination": "Berguedà",
  "category": "Familiar",
  "total": "Berguedà (Comarca) · 19 resultats",
  "results": [
    {
      "title": "Pack Familiar (Muntanya de Sal i Castell de Cardona)",
      "location": "Cardona",
      "description": "Pack d'un dia de visites teatralitzades a la Muntanya de Sal i al Castell de Cardona!",
      "url": "/ofertes/pack-familiar-muntanya-sal-cardona",
      "image": "https://..."
    },
    {
      "title": "Sigues apicultor per un dia! - Mel La Caseta",
      "location": "…",
      "description": "A Mel La Caseta som una petita empresa apícola del Berguedà…",
      "url": "/ofertes/…"
    }
  ]
}
```

**Request 2:**

```
GET https://www.femturisme.cat/agenda?ubicacio=Berguedà&data_inici=2026-06-27&data_fi=2026-06-29
```

JSON (fragmento):

```json
{
  "destination": "Berguedà",
  "date_from": "2026-06-27",
  "date_to": "2026-06-29",
  "results": [
    {
      "title": "Festa de Sant Joan a Guardiola de Berguedà",
      "date": "23 de juny",
      "description": "…"
    },
    {
      "title": "Revetlla de Sant Joan a Saldes",
      "date": "Del 23 al 24 de juny",
      "description": "…"
    }
  ]
}
```

### Paso C — Segunda llamada LLM

**Entrada:** historial completo incluyendo ambos `tool_result`.

**Salida (texto):**

> *"Para el fin de semana en el Berguedà en familia te recomiendo el Pack Familiar de la Muntanya de Sal de Cardona, un día de visitas teatralizadas ideal para niños. También puedes vivir la experiencia de apicultor en Mel La Caseta. Además, coincide con las revetllas de Sant Joan en Saldes y Guardiola de Berguedà…"*

### Paso D — Cliente (SSE)

El frontend recibe `tool_call`, `tool_result`, `text_chunk` (stream simulado) y `done`. Renderiza Markdown con `marked`.

---

## 12. Más ejemplos por tipo de pregunta

### Alojamiento

| Pregunta | Tool call | URL resultante |
|----------|-----------|----------------|
| "Hotel en Girona" | `{destination:"Girona", type:"hotel"}` | `/on-dormir?ubicacio=Girona&tipus=hotel` |
| "Camping Costa Brava" | `{destination:"Costa Brava", type:"camping"}` | `/on-dormir?ubicacio=Costa+Brava&tipus=camping` |

### Rutas

| Pregunta | Tool call | URL resultante |
|----------|-----------|----------------|
| "Ruta senderismo Pirineu" | `{destination:"Pirineu", type:"hiking"}` | `/rutes?ubicacio=Pirineu&tipus=A+peu` |
| "Ruta en bici Empordà" | `{destination:"Empordà", type:"bicicleta"}` | `/rutes?ubicacio=Empordà&tipus=En+bicicleta` |

### Experiencias

| Pregunta | Tool call | URL resultante |
|----------|-----------|----------------|
| "Qué hacer en la Costa Brava" | `{destination:"Costa Brava"}` | `/ofertes?ubicacio=Costa+Brava` |
| "Visita guiada Tarragona" | `{destination:"Tarragona", category:"Visites guiades"}` | `/ofertes?ubicacio=Tarragona&tipus=Visites+guiades` |

### Eventos

| Pregunta | Tool call | URL resultante |
|----------|-----------|----------------|
| "Agenda Barcelona este mes" | `{destination:"Barcelona", date_from:"…", date_to:"…"}` | `/agenda?ubicacio=Barcelona&data_inici=…&data_fi=…` |
| "Ferias en Lleida" | `{destination:"Lleida"}` | `/agenda?ubicacio=Lleida` |

### Info práctica (stub)

| Pregunta | Tool call | HTTP |
|----------|-----------|------|
| "Dónde aparcar en Berga" | `{query:"aparcament Berga", location:"Berga"}` | Ninguno |

### Multi-tool en una pregunta

| Pregunta | Tools probables |
|----------|-----------------|
| "Fin de semana en Berguedà: dormir y hacer senderismo" | `search_accommodations` + `search_routes` |
| "Plan familiar Costa Brava: actividades y eventos" | `search_experiences` + `search_events` |

---

## 13. Errores y límites

### Respuesta de error de scraping

Si `fetch_page` falla (timeout, 404, red):

```json
{
  "error": "No s'ha pogut accedir a femturisme.cat",
  "results": []
}
```

El LLM puede comunicar el fallo al usuario o intentar otra tool si quedan iteraciones.

### Límites operativos

| Límite | Valor | Configuración |
|--------|-------|---------------|
| Cards por tool | 6 | Hardcoded en cada `execute()` |
| Iteraciones tool use por mensaje | 5 (default) | `AGENT_MAX_TOOL_ITERATIONS` |
| Timeout HTTP | 15 s | `scraper.py` |
| Historial de sesión | Memoria del proceso | Se pierde al reiniciar |

### Riesgos de calidad

- **`ubicacio` ambiguo:** `Berga` vs `Berguedà` pueden dar resultados distintos.
- **Fechas incorrectas:** el LLM puede calcular mal el fin de semana.
- **`tipus` desconocido:** se pasa tal cual; el sitio puede ignorarlo o devolver 0 resultados.
- **HTML cambia:** selectores `a.ft-card` dejan de funcionar sin aviso.

---

## 14. Qué NO está implementado

| Capacidad | Estado |
|-----------|--------|
| Scrape de ficha individual (`/ofertes/slug`, `/rutes/slug`, …) | No |
| Paginación (página 2, 3…) | No |
| Cache de respuestas HTTP | No |
| Búsqueda full-text en el sitio | No |
| RAG real en `search_local_knowledge` | No (stub) |
| Streaming nativo del LLM | No (simulado) |
| Endpoints fuera de femturisme.cat | No |

Para ampliar cobertura, la vía habitual es **añadir una nueva tool** con su path y selectores, o **scrapear fichas** en una tool dedicada.

---

## 15. Archivos de código

| Archivo | Rol |
|---------|-----|
| `app/services/tools/scraper.py` | HTTP + parsing HTML |
| `app/services/tools/experiences.py` | Tool `/ofertes` |
| `app/services/tools/accommodations.py` | Tool `/on-dormir` |
| `app/services/tools/events.py` | Tool `/agenda` |
| `app/services/tools/routes_tool.py` | Tool `/rutes` |
| `app/services/tools/local_knowledge.py` | Stub RAG |
| `app/services/tools/__init__.py` | Registro `ALL_TOOLS` |
| `app/services/agent_service.py` | Bucle tool use + inyección JSON al LLM |
| `app/services/llm_service.py` | Adapters multi-proveedor |

---

## Documentación relacionada

- [agente.md](./agente.md) — arquitectura general del agente, proveedores LLM, SSE, configuración.
- [plan-integracion.md](./plan-integracion.md) — plan por fases: Python + MySQL, widget, RAG PDFs, chat unificado.
