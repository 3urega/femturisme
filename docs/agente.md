# Arquitectura del agente turístico

Documento técnico para desarrolladores. Describe cómo el agente de femturisme.cat orquesta el LLM, las herramientas y la obtención de datos.

**Documentación relacionada:**
- **[scraping-y-respuestas.md](./scraping-y-respuestas.md)** — referencia completa: HTML → JSON → respuesta, todos los endpoints, parámetros, mapeos, URLs de prueba y ejemplos extremo a extremo.
- **[plan-integracion.md](./plan-integracion.md)** — plan por fases: servicio Python, MySQL, widget femturisme.cat, RAG PDFs, chat unificado.

**Índice rápido:**
- [Visión general](#visión-general) — arquitectura del bucle tool use
- [De la pregunta del usuario a la respuesta](#de-la-pregunta-del-usuario-a-la-respuesta-cómo-funciona-el-scraping) — resumen del scraping (detalle en [scraping-y-respuestas.md](./scraping-y-respuestas.md))
- [Ejemplo completo: Berguedà en familia](#ejemplo-completo-berguedà-en-familia-fin-de-semana)
- [Referencia de endpoints](#referencia-de-endpoints-de-femturismecat) — resumen (tablas completas en [scraping-y-respuestas.md](./scraping-y-respuestas.md))
- [Más ejemplos](#más-ejemplos-de-extremo-a-extremo)
- [AgentService / LLM / Scraping](#agentservice--el-bucle-central) — detalle de implementación

## Visión general

El agente implementa un **bucle de tool use** clásico (patrón ReAct simplificado):

1. El usuario envía un mensaje.
2. El LLM recibe el historial + esquemas de herramientas y decide si responder directamente o invocar una o más tools.
3. Si invoca tools, el backend las ejecuta (scraping en vivo de femturisme.cat), inyecta los resultados en el historial y vuelve a llamar al LLM.
4. Cuando el LLM devuelve texto final, se emite al cliente por SSE.

No hay RAG sobre un corpus propio salvo `search_local_knowledge`, que hoy es un stub. **La fuente de verdad operativa son las páginas públicas de femturisme.cat**, parseadas con `requests` + BeautifulSoup. Para el detalle de cómo el HTML se convierte en respuesta del chat, endpoints y parámetros, ver **[scraping-y-respuestas.md](./scraping-y-respuestas.md)**.

```
┌─────────────┐     POST /api/chat (SSE)      ┌──────────────────┐
│  chat.js    │ ────────────────────────────► │  routes/api.py   │
└─────────────┘                               └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │  AgentService    │
                                              │  (tool loop)     │
                                              └────────┬─────────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              ▼                        ▼                        ▼
                     ┌────────────────┐      ┌─────────────────┐      ┌─────────────────┐
                     │  llm_service   │      │  tools/__init__ │      │  _history dict  │
                     │  (provider)    │      │  execute_tool() │      │  (in-memory)    │
                     └────────────────┘      └────────┬────────┘      └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  scraper.py     │
                                               │  femturisme.cat │
                                               └─────────────────┘
```

---

## Punto de entrada HTTP

### `POST /api/chat`

Definido en `app/routes/api.py`.

| Campo JSON     | Tipo   | Descripción                                      |
|----------------|--------|--------------------------------------------------|
| `message`      | string | Texto del usuario (obligatorio)                  |
| `session_id`   | string | UUID de sesión; si falta, se genera uno nuevo    |

Respuesta: `text/event-stream` con eventos JSON en formato SSE (`data: {...}\n\n`).

### `POST /api/session/reset`

Borra el historial de conversación asociado a un `session_id` en memoria.

---

## AgentService — el bucle central

Archivo: `app/services/agent_service.py`.

### Flujo por turno de usuario

```python
for iteration in range(max_iterations):          # default: 5 (AGENT_MAX_TOOL_ITERATIONS)
    response = llm.chat(messages=history + system, tools=ALL_TOOLS)

    if response.has_tool_calls:
        # 1. Emitir evento tool_call (UI)
        # 2. Ejecutar cada tool → JSON string
        # 3. Emitir evento tool_result (UI)
        # 4. Append assistant turn con bloques tool_use
        # 5. Append user turn con bloques tool_result
        # → siguiente iteración
    else:
        # Respuesta final: stream simulado por chunks → append a history → done
        return
```

### System prompt

Se prepone en cada llamada al LLM (no se persiste en `_history`):

- Rol: asistente turístico de femturisme.cat (Catalunya + Andorra).
- Instrucción de idioma: responder en el idioma del usuario.
- Indica que tiene herramientas para buscar información actualizada.

### Historial de conversación

Almacenamiento: `_history: dict[str, list[dict]]` en memoria del proceso.

**Formato interno canónico: el de Anthropic** (bloques `tool_use` / `tool_result`), independientemente del proveedor LLM. Cada adapter traduce al formato wire del proveedor en `chat()` y devuelve un `LLMResponse` normalizado.

Ejemplo de un ciclo tool use en el historial:

```python
[
  {"role": "user", "content": "Quines rutes hi ha al Berguedà?"},
  {"role": "assistant", "content": [
    {"type": "tool_use", "id": "abc", "name": "search_routes", "input": {"destination": "Berguedà"}}
  ]},
  {"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "abc", "content": "{\"results\": [...]}"}
  ]},
  {"role": "assistant", "content": "Aquí tens algunes rutes recomanades..."}
]
```

**Limitación:** al reiniciar el servidor o escalar horizontalmente se pierde el historial. No hay persistencia en BD.

### Streaming de la respuesta

El LLM devuelve el texto completo de una vez. `_stream_text()` lo parte en chunks de ~4 palabras con `time.sleep(0.03)` para simular streaming. Los proveedores reales **no usan streaming nativo** todavía.

### Eventos SSE emitidos

| `type`        | Cuándo                          | Payload relevante              |
|---------------|---------------------------------|--------------------------------|
| `tool_call`   | Antes de ejecutar una tool      | `tool`, `input`                |
| `tool_result` | Tras ejecutar                   | `tool`, `result` (objeto JSON) |
| `text_chunk`  | Durante respuesta final         | `content`                      |
| `done`        | Fin del turno                   | `full_text`                    |
| `error`       | Excepción en llamada LLM        | `message`                      |

El frontend (`app/static/js/chat.js`) consume estos eventos: muestra spinners por tool, renderiza Markdown con `marked`, y mantiene el `session_id` en `sessionStorage`.

---

## Capa LLM — abstracción de proveedores

Archivo: `app/services/llm_service.py`.

### Tipos compartidos

```python
@dataclass
class ToolCall:
    id: str
    name: str
    input: dict

@dataclass
class LLMResponse:
    stop_reason: str      # 'end_turn' | 'tool_use'
    text: str = ''
    tool_calls: list[ToolCall] = field(default_factory=list)
```

Factory: `build_provider(provider, config)` según `AGENT_LLM_PROVIDER`.

### Proveedores soportados

| Provider    | Clase               | Modelo por defecto              | Notas |
|-------------|---------------------|---------------------------------|-------|
| `dummy`     | `DummyProvider`     | —                               | Sin API key; heurística por keywords |
| `anthropic` | `AnthropicProvider` | `claude-haiku-4-5-20251001`     | Formato nativo; pasa `tools` directamente |
| `openai`    | `OpenAIProvider`    | `gpt-4.1-mini`                  | Convierte historial Anthropic → OpenAI function calling |
| `gemini`    | `GeminiProvider`    | `gemini-3.1-flash-lite`         | Chat object vivo dentro de un `run()`; ver sección Gemini |

Configuración vía variables de entorno con prefijo `AGENT_` (ver `app/config.py` y `.env.example`).

### Cómo el LLM "obtiene" las respuestas

> Pipeline HTML → JSON → segunda llamada LLM, con ejemplos: [scraping-y-respuestas.md](./scraping-y-respuestas.md).

El LLM **no accede a internet**. Solo ve:

1. El system prompt (rol + instrucciones).
2. El historial de mensajes usuario/asistente.
3. Los esquemas JSON de las tools (nombre, descripción, parámetros).
4. Los **resultados JSON** que el backend inserta tras ejecutar cada tool.

El flujo de información es (ver [sección detallada con ejemplos](#de-la-pregunta-del-usuario-a-la-respuesta-cómo-funciona-el-scraping)):

```
Usuario pregunta
    → LLM elige tool + argumentos (destination, category, etc.)
    → Backend ejecuta tool (HTTP GET a femturisme.cat)
    → JSON con cards (título, ubicación, descripción, url, imagen)
    → LLM recibe ese JSON como tool_result
    → LLM redacta respuesta natural citando/seleccionando lo relevante
```

La calidad de la respuesta depende de:
- Qué tool elige el modelo y con qué parámetros.
- Cuántos resultados devuelve el scraper (limit 6 por tool).
- El system prompt y el historial previo.

### DummyProvider — desarrollo sin API

Implementación determinista para pruebas:

1. **Primera llamada:** escanea keywords del último mensaje de usuario contra `_TOOL_KEYWORDS` y devuelve `tool_use` con `destination: "Catalunya"` fijo.
2. **Segunda llamada** (cuando el último mensaje contiene `tool_result`): formatea los primeros 5 items del JSON en Markdown simple.

No usa el LLM real. Útil para validar el pipeline scraper → agente → UI.

### OpenAIProvider — adaptador de historial

`_convert_messages()` traduce el historial Anthropic a mensajes OpenAI:

- `system` → `role: system`
- `user` string → `role: user`
- `assistant` string → `role: assistant`
- Bloques `tool_use` → `assistant` con `tool_calls`
- Bloques `tool_result` → uno o más mensajes `role: tool` con `tool_call_id`

Los schemas Anthropic (`input_schema`) se mapean a `tools[].function.parameters`.

### GeminiProvider — particularidad de thought signatures

Los modelos Gemini con thinking adjuntan `thought_signature` a las `FunctionCall`. Reconstruir el historial desde bloques Anthropic **pierde esas firmas** y provoca 400.

Solución implementada:

- Dentro de un mismo `AgentService.run()`, se mantiene `self._chat` vivo.
- La primera iteración: `start_chat()` con historial "seguro" (solo turnos de texto; se descartan pares tool_use/tool_result de turnos anteriores).
- Iteraciones con tool results: `_send_tool_results()` envía `FunctionResponse` al chat vivo, preservando el estado interno de Gemini.

**Consecuencia:** en conversaciones multi-turno con tools, el contexto de ejecuciones previas de tools no se reinyecta a Gemini; solo persisten las respuestas finales en texto.

---

## Registro de herramientas

Archivo: `app/services/tools/__init__.py`.

Cada módulo exporta:

- `SCHEMA`: dict en formato Anthropic tool (`name`, `description`, `input_schema`).
- `execute(input: dict) -> str`: devuelve **JSON serializado como string**.

`ALL_TOOLS` es la lista pasada al LLM en cada iteración. `execute_tool(name, input)` despacha al executor correspondiente.

El LLM solo ve el `SCHEMA` (nombre, descripción, parámetros). Las URLs y el scraping viven en `execute()` — ver [§4 de scraping-y-respuestas.md](./scraping-y-respuestas.md#4-contrato-llm-schema-vs-implementación-execute).

### Tools disponibles

| Tool                      | Endpoint femturisme     | Propósito                                      |
|---------------------------|-------------------------|------------------------------------------------|
| `search_experiences`      | `/ofertes`              | Actividades, ofertas, experiencias turísticas  |
| `search_accommodations`   | `/on-dormir`            | Hoteles, casas rurales, campings, etc.         |
| `search_events`           | `/agenda`               | Eventos, ferias, conciertos, agenda            |
| `search_routes`           | `/rutes`                  | Rutas a pie, bici, cultura, senderismo         |
| `search_local_knowledge`  | — (stub)                | Info local no estructurada (RAG futuro)        |

---

## De la pregunta del usuario a la respuesta: cómo funciona el scraping

> **Ampliación:** esta sección es un resumen. La referencia completa (segunda llamada al LLM, tabla navegador vs JSON, todos los endpoints, schemas de respuesta, URLs de prueba y ejemplos) está en **[scraping-y-respuestas.md](./scraping-y-respuestas.md)**.

Esta es la parte que suele generar dudas: **el agente no busca en Google ni navega libremente por internet**. Tampoco el LLM "lee" femturisme.cat directamente. Lo que ocurre es un pipeline en tres capas:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CAPA 1 — LLM (razonamiento)                                            │
│  Texto libre del usuario → elige tool(s) + parámetros estructurados     │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  CAPA 2 — Backend (ejecución)                                           │
│  Construye URL con query params → GET HTTP → parsea HTML → JSON         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│  CAPA 3 — LLM (síntesis)                                                │
│  Recibe JSON con tarjetas → redacta recomendación en lenguaje natural   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Idea clave:** femturisme.cat ya expone filtros en la URL (`?ubicacio=...&tipus=...`). Las tools son wrappers que replican lo que haría un usuario en el buscador del sitio, pero automatizado. El LLM solo decide *qué filtro aplicar* a partir de la pregunta.

### Lo que NO hace vs lo que SÍ hace

| NO hace | SÍ hace |
|---------|---------|
| Búsqueda semántica en toda la web | GET a 4 secciones concretas de femturisme.cat |
| Leer la ficha completa de cada experiencia | Extraer resumen de la tarjeta del listado (título, descripción corta, URL) |
| Garantizar que el filtro `ubicacio` coincida con la intención del usuario | Pasar el texto que el LLM infiere; el sitio resuelve la coincidencia |
| Acceder a internet desde el LLM | El backend hace el HTTP; el LLM solo ve JSON |

El LLM **nunca recibe HTML**. Tras el scraping, solo ve JSON (máx. 6 tarjetas por tool) y en una **segunda llamada** redacta la respuesta. Ver [§1 y §2 de scraping-y-respuestas.md](./scraping-y-respuestas.md#1-pipeline-completo-html--json--respuesta).

---

## Ejemplo completo: Berguedà en familia, fin de semana

### Pregunta del usuario

> *"Voy al Berguedà con familia, recomiéndame algo para este fin de semana"*

### Paso 1 — El LLM interpreta la intención

El modelo lee la pregunta junto con los **schemas** de las 5 tools (nombre, descripción, parámetros). No conoce las URLs; solo sabe que `search_experiences` sirve para actividades, `search_events` para agenda, etc.

Extrae entidades implícitas:

| Intención en lenguaje natural | Parámetro de tool | Valor inferido (ejemplo) |
|-------------------------------|-------------------|--------------------------|
| "al Berguedà" | `destination` | `"Berguedà"` |
| "con familia" | `category` | `"Familiar"` |
| "este fin de semana" | `date_from` / `date_to` | `"2026-06-27"` / `"2026-06-29"` (calculado desde la fecha actual) |

En un turno con LLM real, puede invocar **varias tools** en la misma iteración:

```json
[
  {
    "name": "search_experiences",
    "input": { "destination": "Berguedà", "category": "Familiar" }
  },
  {
    "name": "search_events",
    "input": { "destination": "Berguedà", "date_from": "2026-06-27", "date_to": "2026-06-29" }
  }
]
```

### Paso 2 — El backend construye URLs y hace scraping

**Tool 1 — experiencias familiares:**

```
GET https://www.femturisme.cat/ofertes?ubicacio=Berguedà&tipus=Familiar
```

El sitio devuelve HTML con tarjetas filtradas (p. ej. *"Pack Familiar (Muntanya de Sal i Castell de Cardona)"*, *"Sigues apicultor per un dia!"*). El scraper extrae las 6 primeras.

**Tool 2 — eventos del fin de semana:**

```
GET https://www.femturisme.cat/agenda?ubicacio=Berguedà&data_inici=2026-06-27&data_fi=2026-06-29
```

Devuelve eventos como *"Festa de Sant Joan a Guardiola de Berguedà"*, *"Revetlla de Sant Joan a Saldes"*, etc.

### Paso 3 — JSON que recibe el LLM

Cada tool devuelve un string JSON. El agente lo inyecta en el historial como `tool_result`. Ejemplo simplificado de `search_experiences`:

```json
{
  "destination": "Berguedà",
  "category": "Familiar",
  "total": "Berguedà (Comarca) · 19 resultats",
  "results": [
    {
      "id": "12345",
      "title": "Pack Familiar (Muntanya de Sal i Castell de Cardona)",
      "description": "Pack d'un dia de visites teatralitzades a la Muntanya de Sal i al Castell de Cardona!",
      "location": "Cardona",
      "url": "/ofertes/pack-familiar-muntanya-sal-cardona",
      "image": "https://..."
    }
  ]
}
```

### Paso 4 — Respuesta final al usuario

Con ambos JSON en contexto, el LLM redacta algo como:

> *"Para el fin de semana en el Berguedà en familia te recomiendo el Pack Familiar de la Muntanya de Sal de Cardona, ideal para descubrir patrimonio con niños. Además, el sábado hay revetllas de Sant Joan en Saldes y Guardiola de Berguedà..."*

Selecciona, ordena y contextualiza. **No inventa URLs** si el modelo está bien instruido, pero puede parafrasear descripciones.

### Eventos SSE que vería la UI

```
data: {"type":"tool_call","tool":"search_experiences","input":{"destination":"Berguedà","category":"Familiar"}}
data: {"type":"tool_result","tool":"search_experiences","result":{...}}
data: {"type":"tool_call","tool":"search_events","input":{"destination":"Berguedà","date_from":"2026-06-27","date_to":"2026-06-29"}}
data: {"type":"tool_result","tool":"search_events","result":{...}}
data: {"type":"text_chunk","content":"Para el fin de semana..."}
data: {"type":"done","full_text":"Para el fin de semana..."}
```

---

## Referencia de endpoints de femturisme.cat

> **Referencia completa:** tablas por tool, mapeos `_CATEGORY_MAP` / `_TYPE_MAP`, JSON de respuesta, URLs listas para abrir en el navegador → **[scraping-y-respuestas.md §5–§10](./scraping-y-respuestas.md#5-referencia-de-endpoints-femturismecat)**.

Base URL: `https://www.femturisme.cat`

Todas las tools de scraping usan `fetch_page(path, params)` → `requests.get(BASE_URL + path, params=params)`.

### Tabla resumen

| Tool | Path | Query params que envía el agente | Límite resultados |
|------|------|----------------------------------|-------------------|
| `search_experiences` | `/ofertes` | `ubicacio`, `tipus` (opcional) | 6 cards |
| `search_accommodations` | `/on-dormir` | `ubicacio`, `tipus` (opcional) | 6 cards |
| `search_events` | `/agenda` | `ubicacio`, `data_inici`, `data_fi` (opcionales) | 6 cards |
| `search_routes` | `/rutes` | `ubicacio`, `tipus` (opcional) | 6 cards |
| `search_local_knowledge` | — | No hace HTTP (stub) | 5 chunks dummy |

### Parámetros de query string (sitio web)

| Query param | Origen en la tool | Descripción | Ejemplo |
|-------------|-------------------|-------------|---------|
| `ubicacio` | `destination` | Localidad, comarca o zona. El sitio resuelve el match. | `Berguedà`, `Girona`, `Costa Brava` |
| `tipus` | `category` / `type` | Filtro de categoría (experiencias, alojamiento, rutas) | `Familiar`, `hotel`, `A peu` |
| `data_inici` | `date_from` | Fecha inicio agenda (ISO `YYYY-MM-DD`) | `2026-06-27` |
| `data_fi` | `date_to` | Fecha fin agenda (ISO `YYYY-MM-DD`) | `2026-06-29` |

**Nota:** `ubicacio` acepta nombres tal como los entiende femturisme.cat (comarcas, pueblos, regiones). Si el LLM pasa `"Berga"` en lugar de `"Berguedà"`, el sitio puede devolver resultados distintos o menos relevantes.

---

## Detalle por herramienta (parámetros, mapeos y URLs)

### Patrón común (scraping)

```python
params = {'ubicacio': destination, ...}   # filtros opcionales
soup = fetch_page('/ruta', params)
cards = extract_cards(soup, limit=6)
return json.dumps({'destination': ..., 'total': count, 'results': cards})
```

Cada card normalizada:

```python
{
  'id': '...',           # data-el-id del HTML
  'type': '...',         # data-el-type
  'title': '...',        # .ft-card__title
  'location': '...',     # .ft-card__loc (en eventos → se renombra a 'date')
  'description': '...',  # .ft-item-desc
  'url': '/ofertes/...', # href relativo
  'image': 'https://...' # data-wl-img o CSS background
}
```

---

### `search_experiences` → `/ofertes`

**Cuándo la usa el LLM:** "qué hacer", actividades, experiencias, ofertas, gastronomía, visitas guiadas.

| Parámetro tool | Obligatorio | Query param | Valores |
|----------------|-------------|-------------|---------|
| `destination` | Sí | `ubicacio` | Texto libre |
| `category` | No | `tipus` | Ver tabla abajo |

**Mapeo `_CATEGORY_MAP`** (sinónimos → valor del sitio):

| Input del LLM | `tipus` enviado |
|---------------|-----------------|
| `familiar`, `family` | `Familiar` |
| `activitats`, `activities` | `Activitats` |
| `visites`, `guided` | `Visites guiades` |
| `escapades`, `escapes` | `Escapades` |
| `menus`, `gastronomy` | `Menús` |
| Cualquier otro texto | Se pasa tal cual |

**Ejemplos de URL:**

```
/ofertes?ubicacio=Costa+Brava
/ofertes?ubicacio=Berguedà&tipus=Familiar
/ofertes?ubicacio=Girona&tipus=Visites+guiades
```

**Ejemplo pregunta → tool:**

| Pregunta usuario | Tool call esperada |
|------------------|-------------------|
| "Quines experiències hi ha a la Costa Brava?" | `{destination: "Costa Brava"}` |
| "Activitats en família al Pirineu" | `{destination: "Pirineu", category: "Familiar"}` |
| "Vull fer una escapada gastronòmica a Tarragona" | `{destination: "Tarragona", category: "Menús"}` |

---

### `search_accommodations` → `/on-dormir`

**Cuándo la usa el LLM:** dormir, alojamiento, hotel, casa rural, camping.

| Parámetro tool | Obligatorio | Query param | Valores |
|----------------|-------------|-------------|---------|
| `destination` | Sí | `ubicacio` | Texto libre |
| `type` | No | `tipus` | `hotel`, `casa-rural`, `hostal`, `camping`, `apartament` |

**Sin mapeo:** `type` se pasa directamente como `tipus` (debe coincidir con los filtros del sitio).

**Ejemplos de URL:**

```
/on-dormir?ubicacio=Vall+d%27Aran
/on-dormir?ubicacio=Berguedà&tipus=casa-rural
/on-dormir?ubicacio=Barcelona&tipus=hotel
```

**Ejemplo pregunta → tool:**

| Pregunta usuario | Tool call esperada |
|------------------|-------------------|
| "On puc dormir al Pirineu? Busco turisme rural." | `{destination: "Pirineu", type: "casa-rural"}` |
| "Hotels a Girona centre" | `{destination: "Girona", type: "hotel"}` |
| "Camping a la Costa Brava" | `{destination: "Costa Brava", type: "camping"}` |

---

### `search_events` → `/agenda`

**Cuándo la usa el LLM:** eventos, ferias, festivales, agenda, "qué hay este fin de semana".

| Parámetro tool | Obligatorio | Query param | Formato |
|----------------|-------------|-------------|---------|
| `destination` | Sí | `ubicacio` | Texto libre |
| `date_from` | No | `data_inici` | `YYYY-MM-DD` |
| `date_to` | No | `data_fi` | `YYYY-MM-DD` |

**Post-procesado:** en la agenda, la fecha va en `.ft-card__loc`. El backend la mueve al campo `date` del JSON.

**Ejemplos de URL:**

```
/agenda?ubicacio=Barcelona
/agenda?ubicacio=Berguedà&data_inici=2026-06-27&data_fi=2026-06-29
/agenda?ubicacio=Tarragona&data_inici=2026-07-01&data_fi=2026-07-31
```

**Ejemplo pregunta → tool:**

| Pregunta usuario | Tool call esperada |
|------------------|-------------------|
| "Quins events hi ha a Catalunya aquest mes?" | `{destination: "Catalunya", date_from: "2026-06-01", date_to: "2026-06-30"}` |
| "Festivals al Berguedà el cap de setmana" | `{destination: "Berguedà", date_from: "...", date_to: "..."}` |
| "Agenda de fires a Lleida" | `{destination: "Lleida"}` |

**Riesgo:** las fechas las calcula el LLM. Si interpreta mal "este fin de semana", el filtro de agenda será incorrecto.

---

### `search_routes` → `/rutes`

**Cuándo la usa el LLM:** rutas, senderismo, bici, itinerarios culturales.

| Parámetro tool | Obligatorio | Query param | Valores |
|----------------|-------------|-------------|---------|
| `destination` | Sí | `ubicacio` | Texto libre |
| `type` | No | `tipus` | Ver tabla abajo |

**Mapeo `_TYPE_MAP`:**

| Input del LLM | `tipus` enviado |
|---------------|-----------------|
| `hiking`, `walking`, `peu` | `A peu` |
| `cycling`, `bike`, `bicicleta` | `En bicicleta` |
| `culture`, `cultural` | `Cultura` |
| `adventure`, `sport` | `Esports i aventura` |
| `gastro`, `food` | `Gastronomia` |
| `history`, `historia` | `Història` |
| `nature`, `natura` | `Natura` |
| `literary` | `Literària` |
| Valor en catalán exacto | Se pasa tal cual (`A peu`, `Natura`, etc.) |

**Ejemplos de URL:**

```
/rutes?ubicacio=Berguedà
/rutes?ubicacio=Empordà&tipus=A+peu
/rutes?ubicacio=Pirineu&tipus=Natura
```

**Ejemplo pregunta → tool:**

| Pregunta usuario | Tool call esperada |
|------------------|-------------------|
| "Recomana'm una ruta de senderisme fàcil en família" | `{destination: "Catalunya", type: "A peu"}` o destino de conversación previa |
| "Ruta en bici per l'Empordà" | `{destination: "Empordà", type: "En bicicleta"}` |
| "Itinerari cultural a Barcelona" | `{destination: "Barcelona", type: "Cultura"}` |

---

### `search_local_knowledge` → stub (sin HTTP)

**Cuándo la usa el LLM:** parking, horarios, transporte, info práctica que no encaja en listados.

| Parámetro tool | Obligatorio | Descripción |
|----------------|-------------|-------------|
| `query` | Sí | Búsqueda semántica (futuro RAG) |
| `location` | No | Contexto geográfico (default: `"Berguedà"`) |

**Estado actual:** devuelve 5 chunks hardcodeados sobre Berga/Berguedà. No consulta femturisme.cat ni ningún vector store.

**Ejemplo pregunta → tool:**

| Pregunta usuario | Tool call esperada |
|------------------|-------------------|
| "On puc aparcar a Berga?" | `{query: "aparcament Berga", location: "Berga"}` |
| "Horari oficina de turisme del Berguedà" | `{query: "horaris oficina turisme", location: "Berguedà"}` |

---

## Más ejemplos de extremo a extremo

### Ejemplo A — Solo alojamiento

**Pregunta:** *"Busco un hotel en Girona para 2 noches"*

```
LLM → search_accommodations({ destination: "Girona", type: "hotel" })
GET → https://www.femturisme.cat/on-dormir?ubicacio=Girona&tipus=hotel
LLM → "He trobat alguns hotels a Girona: ..."
```

Nota: las tools **no gestionan noches ni disponibilidad**; solo listan lo que hay en femturisme.cat.

---

### Ejemplo B — Ruta + experiencia (multi-tool, multi-iteración)

**Pregunta:** *"Vull fer senderisme i després dinar bé al Berguedà"*

Posible secuencia (depende del LLM):

```
Iteración 1:
  search_routes({ destination: "Berguedà", type: "A peu" })
  search_experiences({ destination: "Berguedà", category: "Menús" })

Iteración 2:
  LLM sintetiza ruta matinal + opciones gastronómicas
```

Hasta `AGENT_MAX_TOOL_ITERATIONS` (default 5) iteraciones por mensaje.

---

### Ejemplo C — Eventos sin destino explícito en la pregunta

**Pregunta:** *"Què puc fer aquest cap de setmana a prop de Barcelona?"*

```
LLM → search_events({ destination: "Barcelona", date_from: "...", date_to: "..." })
     → posiblemente search_experiences({ destination: "Barcelona" })
```

El LLM infiere destino y fechas del contexto temporal ("aquest cap de setmana").

---

### Ejemplo D — Info práctica (stub)

**Pregunta:** *"Com arribo a Berga des de Barcelona?"*

```
LLM → search_local_knowledge({ query: "transport públic Barcelona Berga", location: "Berga" })
Backend → devuelve chunk dummy con info del bus L4 (no scrapeado)
LLM → responde con ese texto
```

---

### Ejemplo E — Pregunta sin tool (respuesta directa)

**Pregunta:** *"Hola, com funciona aquest assistent?"*

```
LLM → stop_reason: end_turn (sin tool_calls)
Respuesta directa desde el system prompt / conocimiento del modelo
```

---

## Modo `dummy`: comportamiento simplificado

Con `AGENT_LLM_PROVIDER=dummy` no hay inferencia real. El flujo es:

1. Escanea keywords en el mensaje (`hotel` → `search_accommodations`, `ruta` → `search_routes`, etc.).
2. Siempre usa `destination: "Catalunya"` (ignora Berguedà, Girona, etc.).
3. Tras recibir `tool_result`, formatea los 5 primeros items en Markdown.

Útil para probar scraper + UI sin API key, **pero no reproduce el comportamiento de un LLM real**.

---

## Capa de scraping

> Detalle de selectores CSS, campos extraídos por tarjeta y transformación HTML → JSON → respuesta del LLM: **[scraping-y-respuestas.md §2–§3](./scraping-y-respuestas.md#3-capa-de-scraping-scraperpy)**.

Archivo: `app/services/tools/scraper.py`.

### `fetch_page(path, params)`

- `GET https://www.femturisme.cat{path}` con User-Agent de navegador y `Accept-Language: ca-ES`.
- Timeout 15s. Devuelve `BeautifulSoup` o `None` en error.

### `extract_cards(soup, limit=8)`

Selecciona `a.ft-card` y normaliza cada card:

```python
{
  'id':          data-el-id,
  'type':        data-el-type,
  'title':       .ft-card__title,
  'location':    .ft-card__loc,
  'description': .ft-item-desc,
  'url':         href,
  'image':       data-wl-img o background-image de .ft-card__media
}
```

### `result_count(soup)`

Lee `.ft-filter-bar__count` (texto tipo "X resultats").

**Nota:** el scraper asume HTML estable. Cambios en el CMS o clases CSS romperían las tools sin aviso.

---

## Configuración relevante

| Variable                    | Default              | Efecto |
|-----------------------------|----------------------|--------|
| `AGENT_LLM_PROVIDER`        | `dummy`              | Proveedor LLM |
| `AGENT_MAX_TOOL_ITERATIONS` | `5`                  | Límite de ciclos tool use por mensaje |
| `AGENT_*_API_KEY`           | —                    | Credenciales por proveedor |
| `AGENT_*_MODEL`             | ver `.env.example`   | Modelo por proveedor |

Si se alcanza `MAX_TOOL_ITERATIONS` sin respuesta final, el agente devuelve un mensaje de error amigable en catalán.

---

## Añadir una nueva herramienta

1. Crear `app/services/tools/mi_tool.py` con `SCHEMA` + `execute()`.
2. Registrar en `app/services/tools/__init__.py`: añadir a `ALL_TOOLS` y `_EXECUTORS`.
3. (Opcional) Añadir label en `chat.js` → `_toolLabel()`.
4. (Opcional) Keywords en `DummyProvider._TOOL_KEYWORDS` si quieres probarla en modo dummy.

El LLM descubrirá la tool automáticamente vía su `description` en el schema.

---

## Limitaciones y decisiones de diseño

| Área | Estado actual |
|------|---------------|
| Persistencia de sesión | Solo memoria del proceso |
| Streaming LLM | Simulado post-hoc, no token streaming real |
| `search_local_knowledge` | Datos hardcodeados |
| Multi-tool en paralelo | Soportado en el loop (varias `tool_calls` por turno), pero cada provider puede limitar |
| Gemini multi-turn con tools | Historial de tool calls previo no rehidratable |
| Autenticación API | Ninguna en `/api/chat` |
| Rate limiting / cache scraping | No implementado |
| Validación de params | Confía en el LLM + query params del sitio |
| Fechas de agenda | Calculadas por el LLM; pueden ser incorrectas |
| Profundidad de scraping | Solo listados; no entra en fichas individuales — ver [§14 scraping-y-respuestas.md](./scraping-y-respuestas.md#14-qué-no-está-implementado) |
| `ubicacio` | Depende de cómo el sitio resuelva el nombre (Berga vs Berguedà) |

---

## Diagrama de secuencia (turno con varias tools)

Ejemplo: *"Voy al Berguedà con familia este fin de semana"*

```
Usuario          API              AgentService       LLM              Tools (scraper)
  │               │                    │              │                    │
  │── message ───►│                    │              │                    │
  │               │── run() ──────────►│              │                    │
  │               │                    │── chat() ───►│                    │
  │               │                    │◄─ tool_use ×2│                    │
  │               │                    │  (experiences + events)           │
  │◄─ tool_call ──│◄─ yield ───────────│              │                    │
  │               │                    │── execute search_experiences ────►│
  │               │                    │◄─ JSON (6 cards familiares) ──────│
  │◄─ tool_result─│◄─ yield ───────────│              │                    │
  │◄─ tool_call ──│◄─ yield ───────────│              │                    │
  │               │                    │── execute search_events ─────────►│
  │               │                    │◄─ JSON (eventos fin de semana) ───│
  │◄─ tool_result─│◄─ yield ───────────│              │                    │
  │               │                    │── chat()+both results ─►│          │
  │               │                    │◄─ end_turn (recomendación) ─│     │
  │◄─ text_chunk ─│◄─ yield (×N) ──────│              │                    │
  │◄─ done ───────│◄─ yield ───────────│              │                    │
```

---

## Archivos clave

| Archivo | Responsabilidad |
|---------|-----------------|
| `app/routes/api.py` | Endpoints HTTP + generador SSE |
| `app/services/agent_service.py` | Bucle tool use, historial, system prompt |
| `app/services/llm_service.py` | Adapters multi-proveedor |
| `app/services/tools/` | Schemas + ejecutores |
| `app/services/tools/scraper.py` | HTTP + parsing HTML |
| `app/static/js/chat.js` | Cliente SSE + UI |
| `app/config.py` | Configuración desde env |
| [scraping-y-respuestas.md](./scraping-y-respuestas.md) | Endpoints, parámetros, HTML→JSON→respuesta |
