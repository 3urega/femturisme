Ya tengo la foto del código. Buenas noticias: **está a medio camino ya, y lo que falta es barato de dejar preparado ahora** — no hay que construir nada de RAG, solo respetar unas fronteras (seams) al escribir la fase MySQL.

## Qué ya te juega a favor

- **Config lista.** `app/config.py` ya tiene `POSTGRES_*`, `EMBEDDING_MODEL` y `DOCUMENT_STORAGE_PATH`. No tocas nada aquí.
- **El schema PostgreSQL ya es genérico** a nivel documento→chunk (`document_chunks` con `content` + `embedding` + `metadata` JSONB). Es reutilizable tal cual.
- **El agente es agnóstico al mecanismo.** `agent_service.py` solo llama `execute_tool(name, input)` y reenvía el JSON. Le da igual si por debajo hay scraping, MySQL o vectores. Esa frontera ya está bien.
- **El hueco de vectores ya existe** conceptualmente en `local_knowledge.py` (los dummy chunks + el comentario del pgvector). Ese es literalmente el punto donde entrará el vector store.

## Las 3 decisiones que sí importan ahora (coste ~0, ahorro grande después)

**1. Mete la capa Repository entre tool y datos.**
Hoy los tools hablan directo con scraping (`from .scraper import ...`). Cuando hagas la fase MySQL, `AGENTS.md` ya te pide crear `app/db/repositories/`. Si los tools llaman a `EstablishmentsRepository.search(...)` en vez de a SQL directo, mañana añadir RAG es cambiar/ampliar el repositorio (o meter uno híbrido SQL+vector) **sin tocar ni el tool ni el agente**. Este es el punto que más te descomplica el futuro.

**2. Un contrato de resultado normalizado con identidad estable.**
Que todos los tools devuelvan la misma forma (el "card + wrapper" de tecnic §6.13) e incluyan **desde ya**, aunque no lo uses:
- `source_type` (`establishment`, `article`, `event`…)
- `source_id` (la PK de MySQL, p.ej. `establiment_general.id`)
- (opcional) `entity_id` para la Fase 2

Es exactamente el par `(source_type, source_id)` que necesitaría la tabla de embeddings polimórfica de la que hablábamos. Si el card ya lo lleva, enlazar catálogo↔RAG luego es gratis.

**3. Aísla TODO acceso a pgvector detrás de un solo módulo.**
Un único `VectorRepository` / `EmbeddingService` que sea el único que sepa de embeddings y pgvector. Los tools piden "búscame chunks de X"; no saben de coseno ni de HNSW. Así, indexar MySQL en el futuro = escribir filas en ese store, sin cambiar la interfaz de recuperación.

Un cuarto punto "gratis": cuando escribas el repositorio MySQL, si tienes un método que convierte una fila en su texto legible (título + descripción concatenados) para el card, **ese mismo `to_text()` lo reutiliza luego el indexador** para generar el `content` a embeder. No lo hagas pensando en RAG; simplemente no lo entierres dentro del SQL.

## Qué NO hacer ahora (evitar sobre-ingeniería)

- No crees el pipeline de embeddings, ni la tabla polimórfica, ni el reindexado. Eso es la fase futura.
- No metas `source_type`/`source_id` como columnas nuevas en PostgreSQL todavía — basta con **dejarlo anotado** como TBD (ya tienes esa sección en `postgre_schema.md`) y con que el DTO de los tools lo transporte.
- No mezcles estrategia (vector vs SQL) dentro del schema del tool: el `input_schema` describe la intención ("busca establecimientos por destino/tipo"), no el motor.

## Resumen

No es que "ya sea fácil por sí solo": es fácil **si en la fase MySQL respetas tres fronteras** — Repository, DTO con `source_type`+`source_id`, y un único punto de acceso a vectores. Son cosas que la arquitectura objetivo (`AGENTS.md`) ya te pide igualmente, así que no es trabajo extra; solo es hacerlo con esa intención. Si las respetas, incorporar RAG sobre MySQL después es aditivo, no una refactorización.

¿Quieres que te esboce (solo como propuesta, sin tocar nada) cómo quedaría la interfaz del `Repository` y del DTO normalizado para que sirvan tanto a la fase MySQL actual como al RAG futuro?