# Documentació — Agent Femturisme

Documentació del projecte de l'assistent turístic per a **femturisme.cat**.

**Agents i desenvolupadors:** abans de planificar o implementar features, llegiu **[../AGENTS.md](../AGENTS.md)** (arrel del repo).

---

## Model de negoci (llegir primer)

| Document | Contingut |
|----------|-----------|
| **[Domini femturisme](client/dominio-femturisme-ca.md)** | Font de veritat: 6 buscadors MySQL + guies PDF, entitats, mapatge |

---

## Documents per a la consultora (client)

**Ordre de lectura recomanat:**

| Ordre | Document | Contingut | Audiència |
|-------|----------|-----------|-----------|
| **0** | **[Domini femturisme](client/dominio-femturisme-ca.md)** | Què és cada tipus de contingut | Tothom |
| **1** | **[Presa de requeriments](client/requeriments.md)** | Visió, RF, fases producte | Client, direcció |
| **2** | **[Disseny funcional](client/funcional.md)** | Comportament agent, entitats, modes | Client, producte |
| **3** | **[Disseny tècnic](client/tecnic.md)** | APIs, repos, desplegament (v2.1) | Devs, ops |
| — | [document-funcional-client-ca.md](client/document-funcional-client-ca.md) | Legacy consultora | Referència |
| — | [especificacio-tecnica-ca.md](client/especificacio-tecnica-ca.md) | Legacy v1.1 | Referència |

**Enviar al client:** domini + document funcional client (PDF/DOCX).  
**Per estimació:** els quatre documents anteriors + [AGENTS.md](../AGENTS.md) per a l'equip tècnic.

---

## Documents interns (equip agent)

| Document | Contingut |
|----------|-----------|
| [Pla d'integració (CA)](plan-integracion-ca.md) | Roadmap per fases — **nota:** catàleg ampliat a 6 tools; veure domini |
| [Resum integració (CA)](pla-integracio-resum-ca.md) | Resum infra (pot estar desactualitzat respecte 6 dominis) |
| [Arquitectura de l'agent](agente.md) | Bucle tool use, LLM, SSE |
| [Referència scraping](scraping-y-respuestas.md) | Prototip 4 tools (legacy) |
| [Mapeig SQL](sql-mapeo.md) | 6 buscadors MySQL — SQL TODO |
| [Schema PostgreSQL agent](postgre_schema.md) | Base documental, chunks, pgvector |
| [Text-to-SQL vs tools](text-to-sql-desventajas.md) | Decisió arquitectònica |

---

## Desenvolupament local

```powershell
pip install -r requirements-docs.txt
mkdocs serve
```

Obre http://127.0.0.1:8000

## Publicar a Vercel Drop

**Opció fàcil (Windows):** doble clic a `build-docs.bat` a l'arrel del projecte.

**O des de PowerShell** (des de l'arrel `agent_femturisme`):

```powershell
.\scripts\build-docs.ps1
```

Després arrossega **només la carpeta `site`** (o `site.zip`) a [vercel.com/drop](https://vercel.com/drop).
