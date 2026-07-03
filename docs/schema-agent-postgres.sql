-- schema-agent-postgres.sql — PostgreSQL de l'agent femturisme (v1.1 borrador)
--
-- Base documental RAG per entitats (ajuntament, diputació, museu, club…).
-- Documentació: docs/postgre_schema.md
--
-- Requisits: PostgreSQL 15+ amb extensió pgvector.
-- Model d'embedding v1: text-embedding-3-small (1536 dimensions).

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Tipus d'entitat (client del servei / àmbit de coneixement)
-- ---------------------------------------------------------------------------
CREATE TYPE entity_type AS ENUM (
    'ajuntament',
    'diputacio',
    'poblacio',
    'museu',
    'fira',
    'establiment',
    'oficina_turisme',
    'club',
    'altres'
);

-- ---------------------------------------------------------------------------
-- Estat del pipeline d'indexació documental
-- ---------------------------------------------------------------------------
CREATE TYPE guide_document_status AS ENUM (
    'pending',
    'extracting',
    'chunking',
    'embedding',
    'indexed',
    'failed'
);

-- ---------------------------------------------------------------------------
-- Entitats — base de coneixement independent per client
-- ---------------------------------------------------------------------------
CREATE TABLE entities (
    entity_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    entity_type entity_type NOT NULL,
    slug        VARCHAR(255),
    territory   VARCHAR(255),
    config      JSONB NOT NULL DEFAULT '{}',
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT entities_slug_unique UNIQUE (slug)
);

COMMENT ON TABLE entities IS
    'Clients/àmbits amb base de coneixement pròpia (RAG).';
COMMENT ON COLUMN entities.config IS
    'Configuració mode entitat: identitat, tools, enllaços CMS.';

CREATE INDEX idx_entities_entity_type ON entities (entity_type);
CREATE INDEX idx_entities_is_active ON entities (is_active) WHERE is_active = true;

-- ---------------------------------------------------------------------------
-- Documents indexats (per entitat)
-- ---------------------------------------------------------------------------
CREATE TABLE guide_documents (
    doc_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id               UUID NOT NULL REFERENCES entities (entity_id) ON DELETE CASCADE,
    title                   TEXT NOT NULL,
    category                VARCHAR(100),
    source_filename         TEXT NOT NULL,
    storage_path            TEXT NOT NULL,
    mime_type               VARCHAR(100) NOT NULL DEFAULT 'application/pdf',
    status                  guide_document_status NOT NULL DEFAULT 'pending',
    error_message           TEXT,
    pages_count             INT NOT NULL DEFAULT 0 CHECK (pages_count >= 0),
    chunks_count            INT NOT NULL DEFAULT 0 CHECK (chunks_count >= 0),
    embedded_chunks_count   INT NOT NULL DEFAULT 0 CHECK (embedded_chunks_count >= 0),
    embedding_model         VARCHAR(100),
    version                 INT NOT NULL DEFAULT 1 CHECK (version >= 1),
    indexed_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE guide_documents IS
    'Metadades i estat del pipeline per a cada document indexat (PDF v1).';
COMMENT ON COLUMN guide_documents.entity_id IS
    'Entitat propietària; filtre principal per RAG en mode entitat.';
COMMENT ON COLUMN guide_documents.storage_path IS
    'Ruta al PDF original al disc (p.ex. data/guides/{doc_id}/original.pdf).';

CREATE INDEX idx_guide_documents_entity_id ON guide_documents (entity_id);
CREATE INDEX idx_guide_documents_status ON guide_documents (status);
CREATE INDEX idx_guide_documents_category ON guide_documents (category)
    WHERE category IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Fragments indexats + vectors (pgvector)
-- ---------------------------------------------------------------------------
CREATE TABLE document_chunks (
    chunk_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id          UUID NOT NULL REFERENCES guide_documents (doc_id) ON DELETE CASCADE,
    entity_id       UUID NOT NULL,
    chunk_index     INT NOT NULL CHECK (chunk_index >= 0),
    page            INT CHECK (page IS NULL OR page >= 1),
    content         TEXT NOT NULL,
    category        VARCHAR(100),
    embedding       vector(1536),
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (doc_id, chunk_index)
);

COMMENT ON TABLE document_chunks IS
    'Fragments i embeddings per cerca semàntica (Tool base de coneixement entitats).';
COMMENT ON COLUMN document_chunks.entity_id IS
    'Denormalitzat des de guide_documents; filtre RAG sense JOIN extra.';

CREATE INDEX idx_document_chunks_doc_id ON document_chunks (doc_id);
CREATE INDEX idx_document_chunks_entity_id ON document_chunks (entity_id);

CREATE INDEX idx_document_chunks_embedding_hnsw
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);

-- ---------------------------------------------------------------------------
-- Triggers updated_at
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_entities_updated_at
    BEFORE UPDATE ON entities
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_guide_documents_updated_at
    BEFORE UPDATE ON guide_documents
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
