# Pla d'integració — resum per a l'equip

Document curt. El pla detallat per fases està a `plan-integracion-ca.md` (referència tècnica).

---

## Què construïm?

Un **xat a femturisme.cat** (globus flotant) que respon preguntes sobre:

1. **Catàleg** — ofertes, allotjaments, agenda, rutes (dades de la web, via MySQL).
2. **Guies PDF** — fulletons municipals indexats (via PostgreSQL + vectors).

Un sol xat per a l'usuari. Darrere hi ha un **servei Python** amb LLM i tools.

---

## Arquitectura en una imatge

![Diagrama d'arquitectura](assets/diagrama-arquitectura.png)

**Fitxer per Google Docs:** `docs/assets/diagrama-arquitectura.png` (inserir com a imatge; també hi ha `diagrama-arquitectura.svg` per editar).

**Recomanat:** PostgreSQL **gestionat per una plataforma externa** (backups, panel, monitoring). El Docker de l'agent només porta el **Python**.

---

## Dues bases de dades — resposta directa

| | **MySQL femturisme** | **PostgreSQL agent** |
|---|----------------------|----------------------|
| **Ja existeix?** | Sí (la web actual) | **No — cal crear-la** |
| **On viu?** | Servidor femturisme (com ara) | **Plataforma externa** (recomanat) o Docker només a dev local |
| **Read/write?** | **Només lectura** (`agent_read`) | **Lectura i escriptura** (`agent_app`) |
| **Per a què?** | Tools de catàleg (4 cerques SQL) | PDFs pujats, estat indexació, embeddings |
| **Qui l'escriu?** | El CMS PHP (com sempre) | **Només el servei Python** |

**No barregem res:** la MySQL de femturisme no guarda PDFs ni vectors. La PostgreSQL de l'agent no toca el catàleg de la web.

---

## PostgreSQL: Docker vs plataforma externa

| | **PostgreSQL al Docker** | **PostgreSQL gestionat (recomanat)** |
|---|--------------------------|--------------------------------------|
| **Backups** | Cal configurar-los vosaltres | Automàtics des del panell |
| **Monitoring / alertes** | Cal muntar-ho | Inclòs o integrat |
| **pgvector** | Imatge `pgvector/pgvector` | Verificar que el proveïdor el suporta (Supabase, Neon, RDS…) |
| **Staging + producció** | Dos contenidors / manual | Dos projectes o instàncies des del panell |
| **Qui ho gestiona** | Ops + dev (servidor) | Equip via web del proveïdor + credencials a `.env` |
| **Millor per** | Dev local, prova ràpida | **Staging i producció** |

**Recomanació v1:** Python al Docker del vostre servidor; PostgreSQL a un servei gestionat. El Python només necessita la **URL de connexió** (`POSTGRES_HOST`, etc.) al `.env`.

**Exemples de plataformes** (triar una a Fase 0; cal **pgvector**):

- **Supabase** — PostgreSQL + panell + pgvector; fàcil per equips petits
- **Neon** — PostgreSQL serverless, pgvector
- **AWS RDS / Azure Database** — si ja teniu cloud corporatiu

**Què es gestiona des del panell extern:** backups, restauració, mètriques d'espai, usuaris BD, rotació de contrasenyes. **Què es gestiona des del panell Python (`/admin/guides`):** quins PDFs hi ha i si estan indexats — són coses diferents.

---

## Docker — què hi ha dins?

**Staging / producció (recomanat):**

```yaml
services:
  agent:          # Python + Flask (API xat + panell admin PDFs)
  # PostgreSQL: NO aquí → URL externa al .env
```

**Dev local (opcional):**

```yaml
services:
  agent:
  postgres:       # pgvector només per desenvolupament
```

- **Python** exposa: `/api/chat`, `/admin/guides`, `/health`
- **PostgreSQL** (extern): connexió per HTTPS des del contenidor; IP allowlist o SSL al proveïdor
- **MySQL** queda fora; el Python hi connecta per xarxa (VPN/firewall)

Fitxers PDF originals: volum Docker o carpeta `data/guides/` al servidor agent (no van a PostgreSQL; només metadades i vectors).

---

## Què fa cada peça?

| Peça | Rol |
|------|-----|
| **femturisme.cat (PHP)** | Web pública. Globus de xat. Proxy `/api/chat` cap al Python. **No** puja PDFs. **No** executa el LLM. |
| **Python (agent)** | LLM, tools, API xat, panell admin PDFs, pipeline ingest + embeddings. |
| **MySQL** | Font de veritat del catàleg (mateixa BD que la web). |
| **PostgreSQL** | Font de veritat de guies PDF i vectors. |

---

## Dos frontends (no un)

| Qui | On | Què fa |
|-----|-----|--------|
| Visitant | femturisme.cat | Xat turístic |
| Equip femturisme | `https://<agent>/admin/guides` (VPN/intern) | Pujar PDFs, veure si estan indexats |

El Python **té un frontend petit** només per administració de PDFs. No és una segona web pública.

---

## Com es pengen els PDFs?

1. Entrar al panell admin (URL interna del servei Python).
2. Omplir: fitxer PDF + municipi + títol.
3. Clic «Pujar» → el Python desa el fitxer i arrenca el pipeline automàtic.

**Alternativa dev:** `python scripts/ingest_pdf.py --file guia.pdf --municipality Berga`

### On es guarda el fitxer PDF? (cal?)

**Sí, cal guardar-lo.** En pujar, es desen **tres coses** en llocs diferents:

| Què | On | Per a què |
|-----|-----|-----------|
| **PDF original** (fitxer `.pdf`) | Disc del servidor agent: `data/guides/{doc_id}/original.pdf` | Font original; reindexar si canvia el model d'embedding; auditar; tornar a descarregar |
| **Metadades i estat** | PostgreSQL (`guide_documents`) | Títol, municipi, status, errors, comptadors |
| **Text + vectors** | PostgreSQL (pgvector) | Cerca RAG al xat |

El PDF **no** va dins PostgreSQL (seria pesat i poc pràctic). **No** va a MySQL femturisme. **No** va al panell de Supabase/Neon com a fitxer — només la connexió SQL.

**Per què no n'hi ha prou amb els embeddings?**  
Si milloreu chunking o canvieu model d'embedding, cal el PDF per **reindexar** sense tornar a demanar el fitxer a l'equip. Si es perd el PDF, només queda el text ja fragmentat (difícil de reconstruir bé).

**Backups:** cal incloure `data/guides/` **i** PostgreSQL (ops Fase 0/8).

---

## Com sabem quins PDFs hi ha i si l'embedding ha anat bé?

Al panell admin es veu una **taula** amb cada document:

| Camp visible | Exemple |
|--------------|---------|
| Títol / municipi | Guia Berga 2024 — Berga |
| **Estat** | `indexed` ✅ o `failed` ❌ |
| Pàgines / chunks | 48 pàgines, 120 chunks |
| Embeddings | 120/120 (ha de coincidir) |
| Error | (buit si tot OK) |

**Estats:**

- `pending` → `extracting` → `chunking` → `embedding` → **`indexed`**
- Si falla → **`failed`** + missatge d'error + botó «Reindexar»

**Ha anat bé quan:** `status = indexed` i `embeddings = chunks` (tots).

**Prova ràpida:** botó «Provar cerca» al panell, o preguntar al xat: *«On dinar a Berga segons la guia?»*

---

## Com funciona el catàleg (MySQL)?

El LLM **no escriu SQL lliure**. Tria una tool amb paràmetres:

```
Usuari: "Activitats familiars al Berguedà"
    → search_experiences(destination="Berguedà", category="Familiar")
    → Python executa SQL fixa (revisada per devs)
    → JSON amb resultats → LLM respon
```

Per què no SQL al vol? Seguretat, schema legacy, resultats estables, tests. Detall: `plan-integracion-ca.md` Annex D.

---

## Què cal abans de programar (Fase 0)?

Checklist mínim per a ops + dev:

- [ ] Usuari MySQL `agent_read` (només SELECT)
- [ ] `docs/schema.sql` exportat i commitejat (estructura MySQL, sense dades)
- [ ] Compte PostgreSQL gestionat (staging) amb pgvector activat
- [ ] Docker amb **només Python** a staging (o dev local amb postgres opcional)
- [ ] Credencials a `.env` (MySQL + `POSTGRES_*` URL externa)
- [ ] Xarxa: contenidor Python → MySQL femturisme
- [ ] Xarxa: femturisme.cat (proxy) → contenidor Python

---

## Fases (una línia cadascuna)

| # | Què |
|---|-----|
| 0 | Infra: MySQL read-only, PostgreSQL gestionat, Docker Python, `.env` |
| 1 | Python desplegat, `/api/chat` funciona |
| 2 | Documentar SQL per a les 4 tools de catàleg |
| 3 | Implementar tools catàleg contra MySQL |
| 4 | Globus de xat a femturisme.cat |
| 5 | Panell admin PDFs + pipeline embeddings |
| 6 | Tool RAG (cerca a les guies) |
| 7 | Un sol xat: catàleg + guies junts |
| 8 | Producció: logs, límits, backups |

Les fases 2–3 (SQL) i 5 (PDFs) poden anar **en paral·lel** un cop la 0–1 estan llestes.

---

## Decisions preses

| Tema | Decisió |
|------|---------|
| Xat on? | Incrustat a femturisme.cat (mateix domini) |
| Agent on? | Servidor propi, Docker |
| Catàleg | MySQL read-only, tools SQL parametritzades |
| Guies PDF | PostgreSQL gestionat (extern) + pgvector; Python al Docker |
| Pujada PDFs | Panell admin al Python (intern), no al PHP |
| SQL al vol pel LLM | **No** en v1 |

---

## Preguntes freqüents (respostes curtes)

**¿El PHP ha de canviar molt?**  
Globus + proxy cap al Python. Res de PDFs ni LLM al PHP.

**¿Cal tocar la MySQL de producció?**  
Només crear un usuari read-only. Cap escriptura des de l'agent.

**¿PostgreSQL al Docker o extern?**  
**Extern (recomanat)** per staging/producció: backups i gestió des del panell del proveïdor. Docker només per dev local.

**¿On es desplega el Docker?**  
Servidor acordat amb ops (pot ser el mateix host que PHP o un de dedicat). Cal accés des de femturisme.cat al port de l'agent.

**¿Què és `docs/schema.sql`?**  
Volcat de l'estructura MySQL (CREATE TABLE), sense dades. Va al repo de l'agent perquè els devs vegin les taules sense connectar a producció.

**¿I si un PDF falla?**  
Es veu `failed` al panell, es llegeix l'error, es clica Reindexar.

**¿Es guarda el PDF o només els embeddings?**  
Es guarda **el PDF original** al servidor agent (`data/guides/…`) **i** a PostgreSQL el text indexat + vectors. Calen els dos.

---

## Següent pas concret

1. Ops: usuari MySQL read-only + compte PostgreSQL gestionat (staging, pgvector).
2. Dev: Docker amb Python; `.env` apuntant a PostgreSQL extern (o postgres local per provar).
3. Dev: primera connexió MySQL + primera tool de catàleg (`search_experiences`).
