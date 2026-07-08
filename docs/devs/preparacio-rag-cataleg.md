# preparacio-rag-cataleg.md — Deixar el sistema preparat per a RAG sobre el catàleg MySQL

Decisió de disseny **congelada** perquè no calgui tornar-la a pensar quan s'implementi.

| Camp | Valor |
|------|-------|
| **Estat** | Futur (Fase producte 2+). **No** s'implementa a la fase MySQL actual (Fase 3). |
| **Objectiu del doc** | Que incorporar RAG semàntic sobre les taules del catàleg sigui **additiu**, no una refactorització. |
| **Decisió v1 vigent** | El catàleg MySQL es consulta amb **6 tools parametritzades** (SQL estructurada). RAG **només** per a guies PDF (`search_municipality_guides`). Veure [AGENTS.md](../../AGENTS.md) §6 i [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md). |
| **Fonts** | [postgre_schema.md](../postgre_schema.md), [schema-agent-postgres.sql](../schema-agent-postgres.sql), [sql-mapeo.md](../sql-mapeo.md), [arquitectura/patrones-y-convenciones.md](../arquitectura/patrones-y-convenciones.md) |

---

## 1. Principi: **cap equivalència de taules 1:1**

Per fer embeddings + cerca semàntica de les taules MySQL **no** cal replicar cada taula MySQL a PostgreSQL. Seria el pitjor disseny (manteniment, índexs HNSW duplicats, JOINs creuats).

A la capa de vectors **no li importa** de quina taula ve el text. Només necessita 4 coses per fragment:

1. **El text** a indexar (`content`)
2. **El vector** (`embedding`)
3. **D'on ha sortit** (per enllaçar de tornada i filtrar)
4. **Metadades** per filtrar/rankejar (`metadata`)

L'esquema PostgreSQL actual (`entities → guide_documents → document_chunks`) **ja és genèric** a nivell document→chunk i és reutilitzable tal com és.

### Patró: taula de chunks polimòrfica

En lloc de N taules, una sola taula de fragments amb un discriminador d'origen. Cada domini MySQL s'identifica amb el parell **`(source_type, source_id)`**, no amb una taula pròpia.

| Origen MySQL | `source_type` | `source_id` (PK MySQL) |
|--------------|---------------|------------------------|
| `establiment_general` | `establishment` | `id` |
| `noticia_general` | `article` | `id` |
| `poble_general` | `destination` | `id` |
| `ruta_general` | `route` | `id` |
| `agenda_general` | `event` | `id` |
| `oferta_general` | `experience` | `id` |
| PDF (ja implementat) | `guide_pdf` | `doc_id` / `chunk_id` |

> Aquestes columnes (`source_type`, `source_id`) **encara no** s'afegeixen a PostgreSQL. Queden com a **TBD** aquí i a [postgre_schema.md](../postgre_schema.md); n'hi ha prou que el DTO dels tools les transporti (§4).

---

## 2. Quins camps s'embeben: dos cubs, no un

Per cada taula, les columnes es classifiquen en **dos cubs diferents**. Aquesta és la decisió clau i s'ha de fer **per font**.

| Cub | Per a què | Què hi va |
|-----|-----------|-----------|
| **Text a embedir** (`content`) | Similitud semàntica | Només **text lliure semàntic**: títols, introduccions, descripcions, cos d'article |
| **Metadades** (`metadata` / columnes) | Filtratge dur + enllaçar de tornada | IDs, dates, URLs, codis de tipus, comarca, preu… |

**Regla:** només s'embeben els camps de **text lliure**. IDs, dates, URLs i codis **no** s'embeben (introdueixen soroll al vector); van a `metadata` per filtrar.

La llista de camps rellevants per buscador **ja està decidida** a [sql-mapeo.md](../sql-mapeo.md). Per a RAG només cal **etiquetar** quins d'aquells camps són *semàntics* (`content`) i quins són *filtre* (`metadata`).

---

## 3. Projecció per domini (`content` vs `metadata`)

Font dels camps: [sql-mapeo.md](../sql-mapeo.md) §1–6. Els noms són les columnes MySQL (àlies de la query borrador).

### 3.1 `search_establishments` — `source_type = establishment`
| Cub | Camps |
|-----|-------|
| **content** | `nom`, `establiment_continguts.introduccio`, `establiment_continguts.description` |
| **metadata** | `location` (poble), `comarca`, `type` (`generic_tipus_establiment.tipus_ca`/`code`), `url` (`param_url` + prefix), `image` |

### 3.2 `search_articles` — `source_type = article`
| Cub | Camps |
|-----|-------|
| **content** | `noticia_continguts.titol`, `noticia_continguts.cos` |
| **metadata** | `url` (`param_url`), `date` (`data`), `location` (poble), `image` |

### 3.3 `search_destinations` — `source_type = destination`
| Cub | Camps |
|-----|-------|
| **content** | `poble`, `poble_continguts.description`, `poble_continguts.keywords` |
| **metadata** | `url` (`param_url`), `region`/`comarca`, `image` |

### 3.4 `search_routes` — `source_type = route`
| Cub | Camps |
|-----|-------|
| **content** | `ruta_continguts.titol`, `ruta_continguts.introduccio`, `ruta_continguts.description` |
| **metadata** | `url` (`param_url`), `route_type` (`generic_tematiques.tematica_ca`), `location`/`comarca`, `image` |

### 3.5 `search_events` — `source_type = event`
| Cub | Camps |
|-----|-------|
| **content** | `agenda_continguts.titol`, `agenda_continguts.descripcio` |
| **metadata** | `url` (`param_url`), `date_start`/`date_end` (`agenda_dates`), `location`, `image` |

> **Cas clàssic de filtre estructurat:** les dates de l'agenda **mai** s'embeben; han de ser filtre dur (`WHERE data_final >= :date_from …`). El vector no resol bé «aquest cap de setmana».

### 3.6 `search_experiences` — `source_type = experience`
| Cub | Camps |
|-----|-------|
| **content** | `oferta_continguts.titol`, `oferta_continguts.resum`, `oferta_continguts.descripcio` |
| **metadata** | `url` (`param_url`), `category` (`generic_categoria_oferta.categoria_ca`), `establishment_name`, `location`, `price` (`preu_oferta`), vigència (`data_inicial`/`data_final`), `image` |

### 3.7 `guide_pdf` — `source_type = guide_pdf` (ja implementat)
| Cub | Camps |
|-----|-------|
| **content** | text del fragment del PDF |
| **metadata** | `entity_name`, `doc_title`, `source_file`, `page`, `embedding_model`, `indexed_at` |

---

## 4. On viu la decisió: la projecció al Repository

La decisió «quins camps s'embeben de cada taula» **no** viu al vector store ni a l'esquema PostgreSQL (que són genèrics a propòsit), ni al tool, ni a l'agent. Viu **al costat del repositori de cada font**, que ja coneix les columnes de la seva taula.

Cada repositori exposa **dues vistes** de la mateixa fila:

```python
class EstablishmentsRepository:
    SOURCE_TYPE = "establishment"

    def to_card(self, row) -> dict:
        # el que necessites JA a la fase MySQL (resposta del tool)
        ...

    def to_document(self, row) -> dict:
        # el que necessitaria l'indexador FUTUR
        return {
            "source_type": self.SOURCE_TYPE,
            "source_id": row["id"],
            "content": self._embed_text(row),        # ← aquí es decideix QUÈ s'embebe
            "metadata": {
                "destination": row["location"],
                "comarca": row["comarca"],
                "type": row["type_code"],
                "url": build_url(row),
            },
        }

    @staticmethod
    def _embed_text(row) -> str:
        parts = [row["title"], row.get("introduccio"), row.get("description")]
        return "\n".join(p for p in parts if p)
```

`_embed_text()` és **l'únic lloc** on es decideix quins camps d'aquesta taula formen el text embegut. Cada domini té el seu (l'agenda concatena títol + descripció però **mai** la data).

> Alternativa equivalent: un registre declaratiu per `source_type` amb `content_fields: [...]` i `metadata_fields: [...]`. Mateix concepte, estil diferent.

---

## 5. Fronteres (seams) a respectar **ara** (cost ~0)

Aquestes decisions ja les demana l'arquitectura objectiu ([AGENTS.md](../../AGENTS.md), [arquitectura/](../arquitectura/)); només cal fer-les amb aquesta intenció.

1. **Capa Repository entre tool i dades.** Els tools criden `EstablishmentsRepository.search(...)`, no SQL directe. Afegir RAG = ampliar el repositori (o un d'híbrid SQL+vector) **sense tocar tool ni agent**.
2. **DTO de resultat normalitzat amb identitat estable.** Tots els tools retornen la mateixa forma (card + wrapper, [tecnic.md §6.13](../client/tecnic.md)) i inclouen **des d'ara** `source_type` + `source_id` (+ `entity_id` opcional per Fase 2), encara que no s'usin.
3. **Aïllar tot accés a pgvector** darrere un únic `VectorRepository`/`EmbeddingService`. Els tools demanen «dona'm chunks de X»; no saben de cosinus ni HNSW.
4. **Reutilitzar `_embed_text()`/`to_document()`.** Si el repositori MySQL ja té un mètode que converteix una fila en text net per al card, l'indexador futur el reutilitza per generar el `content`. No enterrar aquesta lògica dins del SQL.

---

## 6. Què **NO** fer ara (evitar sobre-enginyeria)

- No crear el pipeline d'embeddings, ni la taula polimòrfica, ni el reindexat.
- No afegir `source_type`/`source_id` com a columnes noves a PostgreSQL encara (queda TBD).
- No barrejar l'estratègia (vector vs SQL) dins del `input_schema` del tool: descriu la **intenció**, no el motor.

---

## 7. Punts oberts per a la implementació futura

| Tema | Nota |
|------|------|
| **Staleness / sincronització** | MySQL és contingut viu (CMS). RAG necessita un pipeline de reindexat (detecció de canvis, upsert/delete de chunks per `(source_type, source_id)`). Les tools parametritzades llegeixen sempre dada fresca. |
| **Cerca híbrida** | Els filtres durs (dates agenda, vigència ofertes, tipus, comarca) es resolen amb `WHERE` sobre `metadata`/columnes + similitud vectorial. No només cosinus. |
| **Chunking de text curt** | Fitxes de catàleg solen ser curtes: potser 1 chunk per fila (no cal fragmentar com els PDF). Validar a implementació. |
| **`entity_id` a MySQL (Q-08)** | No apareix al schema MySQL; enllaç catàleg↔entitat és Fase 2. Veure [dominio-femturisme-ca.md §7](../client/dominio-femturisme-ca.md). |
| **Cost d'embeddings** | Reindexar tot el catàleg té cost per token; planificar batch + només camps de `content`. |

---

## 8. Resum d'una línia

No cal 1:1 de taules; una taula de chunks polimòrfica amb `(source_type, source_id)`. **Quins camps s'embeben** es decideix per font, dins el `to_document()`/`_embed_text()` del seu Repository, embebent **només text lliure** i deixant IDs/dates/URLs com a `metadata`. Si a la Fase 3 es respecten les 4 fronteres del §5, incorporar RAG després és additiu.
