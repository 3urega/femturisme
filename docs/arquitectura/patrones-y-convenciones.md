# Patrons i convencions de codi

Regles per escriure codi nou al servei agent. Complementa [tecnic.md](../client/tecnic.md) amb decisions implementables.

---

## 1. Estil arquitectònic adoptat

| Enfoc | Decisió |
|-------|---------|
| **DDD estricte** | No — massa pes per un servei d'integració + RAG |
| **Hexagonal / ports** | Parcial — repositories com a adaptadors de sortida |
| **Layered architecture** | Sí — capa principal |
| **Repository pattern** | Sí — obligatori per MySQL i PostgreSQL |
| **Tool registry** | Sí — interfície estable cap al LLM |
| **Strategy (LLM)** | Sí — `BaseLLMProvider` + `build_provider()` |

---

## 2. SOLID aplicat al projecte

### Single Responsibility (SRP)

| Mòdul | Una responsabilitat |
|-------|---------------------|
| `Tool` | Un domini de cerca + contracte SCHEMA |
| `Repository` | Accés a dades d'un agregat tècnic (establiments, events…) |
| `AgentService` | Bucle tool-use i historial — **no** SQL ni prompts llargs inline |
| `llm_service` | Comunicació amb proveïdors LLM |

**Evitar:** `AgentService` amb SYSTEM_PROMPT de 200 línies, SQL i mapatge JSON.

### Open/Closed (OCP)

- **Afegir** un buscador = nou repository + nova tool + entrada al registry. **No** modificar les altres tools.
- **Afegir** provider LLM = nova classe + branca a `build_provider()`.

### Liskov Substitution (LSP)

- Tots els providers implementen `BaseLLMProvider.chat()` → `LLMResponse`.
- Totes les tools implementen `execute(input: dict) -> str` (JSON).

### Interface Segregation (ISP)

- El LLM només ve `SCHEMA` (name, description, input_schema) i JSON de resposta.
- Els repositories no s'exposen al LLM.

### Dependency Inversion (DIP)

**Objectiu (codificar així en codi nou):**

```python
# Bo: repository injectable o obtingut per factory
class ExperiencesTool:
    def __init__(self, repo: ExperiencesRepository):
        self._repo = repo

    def execute(self, tool_input: dict) -> str:
        data = self._repo.search(destination=tool_input["destination"])
        return json.dumps(data)
```

**Evitar en codi nou:**

```python
# Dolent: current_app i imports globals dins la lògica
from flask import current_app
conn = current_app.extensions["mysql"]
```

**Estat actual:** `AgentService` usa `current_app` — acceptable al prototip; refactoritzar quan s'afegeixin tests unitaris.

---

## 3. Contracte d'una Tool

Cada fitxer a `app/services/tools/` exporta:

```python
SCHEMA: dict   # Format Anthropic: name, description, input_schema
execute(tool_input: dict) -> str   # JSON serialitzat; mai text lliure per l'usuari
```

### Plantilla `execute()`

```python
def execute(tool_input: dict) -> str:
    # 1. Validar paràmetres obligatoris
    destination = tool_input.get("destination")
    if not destination:
        return json.dumps({"error": "destination required", "results": []})

    # 2. Cridar repository (no SQL aquí)
    try:
        data = experiences_repo.search(destination=destination, category=tool_input.get("category"))
    except DatabaseError:
        return json.dumps({"error": "No s'ha pogut accedir a les dades del catàleg", "results": []})

    # 3. Retornar wrapper normalitzat
    return json.dumps(data)
```

### Registre

Afegir a `app/services/tools/__init__.py`:

- import `SCHEMA` i `execute`
- entrada a `ALL_TOOLS`
- entrada a `_EXECUTORS`

---

## 4. Contracte d'un Repository

Ubicació: `app/db/repositories/<nom>.py`

```python
def search(*, destination: str, type: str | None = None, limit: int = 20) -> dict:
    """
    Retorna el wrapper JSON complet (destination, total, results[], error).
    SQL fixa amb paràmetres (%s); LIMIT al repository.
    """
```

**Regles SQL:**

- Només `SELECT`
- Paràmetres bindats — **mai** concatenació de strings d'usuari/LLM
- `LIMIT` per defecte 20; truncat a 6 cards abans de tornar al LLM (al servei o al mapper)
- Mapatge fila → card via `app/db/mappers.py`

Documentar cada query a [sql-mapeo.md](../sql-mapeo.md) abans d'implementar.

---

## 5. Card JSON comú

Totes les tools de catàleg retornen cards amb aquest shape mínim:

```json
{
  "id": "string | null",
  "type": "string | null",
  "title": "string",
  "location": "string | null",
  "description": "string | null",
  "url": "string | null",
  "image": "string | null",
  "date": "string | null",
  "entity_id": "uuid | null"
}
```

Wrapper:

```json
{
  "destination": "...",
  "total": "12",
  "results": [],
  "error": null
}
```

---

## 6. Gestió d'errors

| Capa | Comportament |
|------|--------------|
| Repository | Excepcions tipades (`DatabaseError`) o resultat buit |
| Tool | JSON amb `error` amigable; **mai** stack trace al LLM |
| AgentService | Event SSE `error` per fallades irrecuperables |
| Routes | HTTP 400 validació; 500 només errors no controlats |

---

## 7. Convencions Python

| Tema | Convenció |
|------|-----------|
| Idioma codi | Anglès (noms de funcions, variables, fitxers) |
| Comentaris | Anglès o català segons el fitxer existent |
| Type hints | Obligatoris en codi nou (`def search(*, destination: str) -> dict`) |
| Imports | Absoluts des de `app.` |
| Tests | `pytest`; integració SQL amb `@pytest.mark.integration` |
| Secrets | Només `.env`; mai al repo |

---

## 8. Testing (obligatori en codi nou de repositories)

```
tests/
├── conftest.py              # app fixture, app_context
├── unit/
│   └── test_mappers.py
└── integration/
    └── sql/
        └── test_experiences.py
```

Mínim per cada repository:

- Cas amb resultats (documentat a sql-mapeo.md)
- Cas sense resultats
- URL vàlida quan hi ha resultats

---

## 9. Anti-patterns (no generar codi així)

| Anti-pattern | Per què |
|--------------|---------|
| Scraping HTML com a font permanent | Legacy; substituir per MySQL |
| `execute_sql` genèric per al LLM | Prohibit en producció |
| SQL dins `tools/` o `agent_service.py` | Trenca SRP i testabilitat |
| RAG «general» en mode femturisme | Només amb `entity_id` a resultats (Fase 2) |
| Estat global mutable sense documentar | Historial ha d'anar a Redis/BD si multi-instància |
| Canviar nom de Tool sense actualitzar prompt/tests | Trenca routing |

---

## 10. Checklist abans de merge (codi nou)

- [ ] SQL documentada a `sql-mapeo.md` (si afecta MySQL)
- [ ] Repository amb paràmetres bindats i LIMIT
- [ ] Tool retorna JSON normalitzat
- [ ] Registrada a `ALL_TOOLS` si és nova
- [ ] Test d'integració o unitari afegit
- [ ] No importa `scraper.py` (salvo treball explícit legacy)
- [ ] Respecta mode operatiu (femturisme / entitat)
- [ ] CA aplicables de requeriments verificables
