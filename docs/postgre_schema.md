# postgre_schema — PostgreSQL de l'agent

Model físic de la base documental (RAG per **entitats**). DDL: [schema-agent-postgres.sql](schema-agent-postgres.sql).

**Requisits:** PostgreSQL 15+ amb extensió `pgvector`.  
**Embedding v1:** `text-embedding-3-small` → `vector(1536)`.  
**PDF original:** disc `data/guides/{doc_id}/original.pdf` (no a PostgreSQL).

Font funcional: [funcional.md](client/funcional.md) §8.4, §14–15 · [requeriments.md](client/requeriments.md) RF-13, RF-14, RF-15.

---

## Relació entre taules

```
entities (1) ──< guide_documents (1) ──< document_chunks (N)
     │                    ON DELETE CASCADE
     └──────────────────── (entity_id denormalitzat als chunks)
```

Només es consulten chunks de documents amb `guide_documents.status = 'indexed'`.

Cerca RAG en **mode entitat**: filtrar per `entity_id` de l'entitat activa.  
Cerca RAG en **mode femturisme**: filtrar per `entity_id` quan l'element del portal té associació (Fase 2, MySQL).

---

## Tipus `entity_type`

Valors previstos (ampliables):

| Valor | Exemple |
|-------|---------|
| `ajuntament` | Ajuntament de Berga |
| `diputacio` | Diputació de Barcelona |
| `poblacio` | Municipi com a client |
| `museu` | Museu de Bagà |
| `fira` | Fira de Sant Jordi |
| `establiment` | Hotel, restaurant… |
| `oficina_turisme` | OT municipal |
| `club` | Club esportiu, entitat cultural… |
| `altres` | Resta de clients |

---

## Tipus `guide_document_status`

| Valor | Descripció |
|-------|------------|
| `pending` | Registrat; pipeline no iniciat |
| `extracting` | Extracció de text del PDF |
| `chunking` | Fragmentació (500–1000 tokens, overlap 10–15 %) |
| `embedding` | Generació de vectors |
| `indexed` | Indexació completa; disponible per RAG |
| `failed` | Error; veure `error_message` |

---

## Taula `entities`

Una fila per client / àmbit amb base de coneixement pròpia (ajuntament, diputació, club, museu…).

| Camp | Tipus | Null | Descripció |
|------|-------|------|------------|
| `entity_id` | UUID | PK | Identificador de l'entitat |
| `name` | TEXT | NOT NULL | Nom visible (p.ex. «Museu de Bagà») |
| `entity_type` | `entity_type` | NOT NULL | Tipus d'entitat |
| `slug` | VARCHAR(255) | Sí | Identificador estable per URL/widget (únic si informat) |
| `territory` | VARCHAR(255) | Sí | Àmbit geogràfic opcional (municipi, comarca…) |
| `config` | JSONB | NOT NULL | Configuració mode entitat (identitat, tools habilitades…) |
| `is_active` | BOOLEAN | NOT NULL | Entitat operativa |
| `created_at` | TIMESTAMPTZ | NOT NULL | Alta |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Darrera actualització |

**Índexs:** `entity_type`, `slug` (únic parcial), `is_active`.

**Relació amb el portal (Fase 2):** elements MySQL poden portar el mateix `entity_id` (UUID) per enllaçar catàleg i RAG ([requeriments.md](client/requeriments.md) RF-15).

---

## Taula `guide_documents`

Un fitxer pujat = una fila. Pertany a **una entitat**.

| Camp | Tipus | Null | Descripció |
|------|-------|------|------------|
| `doc_id` | UUID | PK | Identificador del document |
| `entity_id` | UUID | FK → `entities` | Entitat propietària del document |
| `title` | TEXT | NOT NULL | Títol visible |
| `category` | VARCHAR(100) | Sí | Categoria opcional (patrimoni, festes, museu…) |
| `source_filename` | TEXT | NOT NULL | Nom del fitxer original |
| `storage_path` | TEXT | NOT NULL | Ruta al PDF al disc |
| `mime_type` | VARCHAR(100) | NOT NULL | v1: `application/pdf` |
| `status` | `guide_document_status` | NOT NULL | Estat del pipeline |
| `error_message` | TEXT | Sí | Detall d'error quan `status = failed` |
| `pages_count` | INT | NOT NULL | Pàgines extretes del PDF |
| `chunks_count` | INT | NOT NULL | Fragments generats |
| `embedded_chunks_count` | INT | NOT NULL | Fragments amb embedding creat |
| `embedding_model` | VARCHAR(100) | Sí | Model usat per indexar |
| `version` | INT | NOT NULL | Incrementa en cada reindexació |
| `indexed_at` | TIMESTAMPTZ | Sí | Timestamp de fi d'indexació correcta |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creació del registre |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Darrera actualització |

**Índexs:** `entity_id`, `status`, `category` (parcial, si no null).

**Indexació correcta:** `status = indexed`, `pages_count > 0`, `chunks_count > 0`, `embedded_chunks_count = chunks_count`, `error_message IS NULL`, `indexed_at` informat.

**Delete entitat:** `ON DELETE CASCADE` esborra documents i chunks associats.

---

## Taula `document_chunks`

Fragments de text indexats per cerca semàntica dins la base de coneixement d'una entitat.

| Camp | Tipus | Null | Descripció |
|------|-------|------|------------|
| `chunk_id` | UUID | PK | Identificador del fragment |
| `doc_id` | UUID | FK → `guide_documents` | Document pare; CASCADE en delete |
| `entity_id` | UUID | NOT NULL | Copiat del document; filtre RAG sense JOIN |
| `chunk_index` | INT | NOT NULL | Ordre dins del document; únic per `(doc_id, chunk_index)` |
| `page` | INT | Sí | Número de pàgina al PDF |
| `content` | TEXT | NOT NULL | Text del fragment |
| `category` | VARCHAR(100) | Sí | Categoria del fragment o del document |
| `embedding` | vector(1536) | Sí | Vector pgvector |
| `metadata` | JSONB | NOT NULL | Metadades addicionals (veure sota) |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creació del chunk |

**Índexs:** `doc_id`, `entity_id`, HNSW sobre `embedding` (cosine).

---

## Camp `entities.config` (JSONB)

Claus previstes per **mode entitat**:

| Clau | Descripció |
|------|------------|
| `display_name` | Nom de l'assistent |
| `welcome_message` | Missatge inicial opcional |
| `allowed_tools` | Llista de tools habilitades en mode entitat |
| `portal_entity_id` | Referència opcional a ID legacy CMS |

---

## Camp `document_chunks.metadata` (JSONB)

| Clau | Descripció |
|------|------------|
| `entity_name` | Nom de l'entitat |
| `doc_title` | Títol del document |
| `source_file` | Nom del fitxer original |
| `embedding_model` | Model d'embedding |
| `indexed_at` | ISO 8601 de la indexació |

Exemple:

```json
{
  "entity_name": "Museu de Bagà",
  "doc_title": "Catàleg exposicions 2024",
  "source_file": "cataleg_museu.pdf",
  "embedding_model": "text-embedding-3-small",
  "indexed_at": "2026-06-23T10:00:00Z"
}
```

---

## Camps pendents de concretar (TBD)

| Camp | Opcions |
|------|---------|
| `entity_type` | Enum tancat vs ampliació per tipus de client |
| `slug` | Obligatori en mode entitat / widget propi |
| `entities.config` | Esquema JSON definitiu amb equip PHP |
| `entity_id` al MySQL | Mateix UUID vs taula de mapatge portal ↔ agent |
| `category` | Text lliure vs taxonomia fixa per entitat |
