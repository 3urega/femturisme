# Especificació funcional — Assistent de xat femturisme.cat (v1.1)

Document de **presa de requeriments** i **especificació funcional** per a l'equip de desenvolupament (consultora / programadors).

| Camp | Valor |
|------|-------|
| **Versió** | 1.1 |
| **Data** | 2026-06-28 |
| **Abast** | v1 — 6 buscadors MySQL + guies PDF |
| **Domini (font de veritat)** | [dominio-femturisme-ca.md](dominio-femturisme-ca.md) |
| **Document per al client** | [document-funcional-client-ca.md](document-funcional-client-ca.md) |
| **Document tècnic** | [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) |

---

## 1. Context i objectiu de negoci

### 1.1 Context

**femturisme.cat** és el portal de turisme de Catalunya i Andorra. El catàleg inclou establiments (dormir/menjar), articles, poblacions («on anar»), rutes, agenda i experiències promocionals.

Es vol un **assistent conversacional** que respongui en llenguatge natural i **derivi tràfic cap a fitxes de femturisme.cat**.

### 1.2 Objectiu

Un **xat únic** que:

1. Consulti el **catàleg MySQL** via **6 buscadors** parametritzats (veure domini §5).
2. Consulti **guies PDF** indexades.
3. Retorni resposta textual + **enllaços** quan hi hagi resultats rellevants.

### 1.3 Exemple representatiu

**Pregunta:** «Què fem aquest cap de setmana a l'Empordà?»

- Consulta **agenda** (`search_events`) amb destinació i dates del cap de setmana.
- Pot complementar amb **experiències** o **on anar** segons la pregunta.
- Resposta amb enllaços a `femturisme.cat/agenda/...`.

---

## 2. Actors i permisos

| Actor | Accés |
|-------|-------|
| **Visitant web** | Globus de xat |
| **Administrador de guies** | Panell `/admin/guides` (intern) |
| **Ops** | Infraestructura, credencials |
| **Desenvolupador PHP** | Widget, proxy, `page_context` |
| **Desenvolupador Python** | Agent, 6 buscadors, PDFs |

---

## 3. Casos d'ús

### CU-01 — Consultar establiments (on dormir / on menjar)

| Camp | Descripció |
|------|------------|
| **Actor** | Visitant |
| **Flux principal** | Pregunta «Hotel a Girona» o «On menjar a Berga» → sistema identifica destinació i tipus → `search_establishments` → resposta amb enllaços. |
| **Flux alternatiu** | Sense resultats / error de servei (missatge clar). |

**Operació:** `search_establishments`

---

### CU-02 — Consultar articles / notícies

| Camp | Descripció |
|------|------------|
| **Flux principal** | Pregunta sobre article o notícia (p.ex. parc natural, Patum) → `search_articles` → enllaços a contingut editorial. |

**Operació:** `search_articles`

---

### CU-03 — Consultar on anar (poblacions / llocs)

| Camp | Descripció |
|------|------------|
| **Flux principal** | Pregunta «Què veure a Besalú» → `search_destinations` → descripció i enllaços a fitxes de població/lloc. |

**Operació:** `search_destinations`

---

### CU-04 — Consultar rutes

| Camp | Descripció |
|------|------------|
| **Flux principal** | Pregunta «Ruta a peu al Pirineu» → `search_routes` → enllaços `/rutes/`. |

**Operació:** `search_routes`

---

### CU-05 — Consultar agenda (esdeveniments de calendari)

| Camp | Descripció |
|------|------------|
| **Flux principal** | «Què fem aquest cap de setmana a l'Empordà?» → `search_events` amb dates → enllaços agenda. |
| **Flux alternatiu** | Sense esdeveniments; dates ambigües (aclariment o cap de setmana per defecte a UAT). |

**Operació:** `search_events`

---

### CU-06 — Consultar experiències promocionals

| Camp | Descripció |
|------|------------|
| **Flux principal** | «Arrossada popular a Olvan» o «Dinar Sant Valentí Berguedà» → `search_experiences` → enllaços a propostes lligades a establiment/població. |
| **Nota** | No confondre amb agenda (RN-009). |

**Operació:** `search_experiences`

---

### CU-07 — Consultar guia municipal (PDF)

| Camp | Descripció |
|------|------------|
| **Flux principal** | «On dinar a Berga segons la guia?» → `search_municipality_guides` → resposta amb font (títol guia, pàgina). |
| **Flux alternatiu** | Sense guia indexada per al municipi. |

**Operació:** `search_municipality_guides`

---

### CU-08 — Pregunta mixta (catàleg + guia)

| Camp | Descripció |
|------|------------|
| **Flux principal** | Combina ≥2 buscadors (p.ex. agenda + guia, establiments + rutes) en una resposta. |

---

### CU-09 — Pujar i indexar PDF (admin)

| Camp | Descripció |
|------|------------|
| **Flux principal** | Admin puja PDF → pipeline → estat `indexed` o `failed`. |

---

### CU-10 — Reiniciar conversa

| Camp | Descripció |
|------|------------|
| **Flux principal** | Nova conversa esborra historial de sessió. |

---

## 4. Requeriments funcionals

### 4.1 Xat públic (RF-01xx)

| ID | Requeriment |
|----|-------------|
| RF-0101 | Globus flotant a totes les pàgines públiques |
| RF-0102 | Panell overlay obrir/tancar |
| RF-0104 | Enviar missatge i rebre resposta |
| RF-0105 | Indicador «Cercant…» durant consultes |
| RF-0106 | Resposta en idioma de l'usuari (ca/es/en) |
| RF-0107 | Reinici de conversa |
| RF-0108 | Resposta llegible amb enllaços clicables |
| RF-0109 | Same-origin via proxy femturisme.cat |

### 4.2 Catàleg — per domini (RF-02xx)

| ID | Requeriment | CU |
|----|-------------|-----|
| RF-0201 | Cerca **establiments** per destinació i tipus (dormir/menjar) | CU-01 |
| RF-0202 | Cerca **articles/notícies** per tema i/o destinació | CU-02 |
| RF-0203 | Cerca **on anar** (poblacions/llocs) per destinació | CU-03 |
| RF-0204 | Cerca **rutes** per destinació i tipus opcional | CU-04 |
| RF-0205 | Cerca **agenda** per destinació i dates opcionals | CU-05 |
| RF-0206 | Cerca **experiències** promocionals per destinació i filtres opcionals | CU-06 |
| RF-0210 | Davant «Què fem aquest cap de setmana a l'Empordà?», consulta agenda amb dates del cap de setmana i retorna enllaços vàlids | CU-05 |
| RF-0211 | Cada resposta de catàleg inclou **enllaços a femturisme.cat** quan hi ha resultats | Tots CU catàleg |
| RF-0212 | Només contingut **publicat i vigent** (RN-001, RN-002) | Tots |
| RF-0213 | Límit de resultats per consulta (RN-004) | Tots |
| RF-0214 | Combinació de **múltiples buscadors** en un torn (CU-08) | CU-08 |
| RF-0215 | Sense resultats → missatge clar sense URLs inventades | Tots |

### 4.3 Guies PDF (RF-03xx)

| ID | Requeriment |
|----|-------------|
| RF-0301 | Respostes basades en guies indexades per municipi |
| RF-0302 | Citar font (títol guia; pàgina si escau) |
| RF-0303 | Només documents `indexed` |
| RF-0304 | Combinació amb catàleg (CU-08) |

### 4.4 Admin PDF (RF-04xx)

| ID | Requeriment |
|----|-------------|
| RF-0401–0407 | Pujada, llistat, detall, reindexar, prova cerca, estats pipeline, panell no públic |

### 4.5 Context pàgina (RF-05xx)

| ID | Requeriment |
|----|-------------|
| RF-0501 | Enviament opcional `page_context` des del PHP |
| RF-0502 | Ús del context per preguntes ambigües |

---

## 5. Regles de negoci

| ID | Regla |
|----|-------|
| RN-001 | Només registres **publicats** |
| RN-002 | Esdeveniments agenda **vigents/futurs** |
| RN-003 | URLs canòniques per secció (confirmar a `sql-mapeo.md`) |
| RN-004 | Màx. 20 files SQL; màx. 6 destacats al xat |
| RN-005 | Agent **no escriu** a MySQL femturisme |
| RN-006 | PDF només si `indexed` |
| RN-007 | Visitant no puja PDFs |
| RN-008 | Catàleg i PDF són fonts independents; resposta unificada |
| RN-009 | **Agenda ≠ experiències:** agenda = calendari; experiències = proposta d'establiment/població |

---

## 6. Requeriments no funcionals (RNF-001–008)

Sense canvis respecte v1.0 (idiomes, proxy, latència, staging/prod, seguretat, privacitat sessió, degradació, mobile).

---

## 7. Abast v1

### Dins

- 6 buscadors MySQL + guies PDF + xat + panell admin.

### Fora

- SQL lliure; CMS des del xat; GPS; admin PHP.

---

## 8. Supòsits

S-01–S-06 sense canvis + **S-07:** el client/mantenedor aclareix schema MySQL per als 6 dominis (dominio §7).

---

## 9. Criteris d'acceptació

### 9.1 Xat (CA-0101–0106)

Sense canvis.

### 9.2 Catàleg — un CA per domini

| ID | Prova | RF |
|----|-------|-----|
| CA-0201 | «Hotel a Girona» → enllaç establiment | RF-0201 |
| CA-0202 | «Restaurant a Pals» → enllaç establiment menjar | RF-0201 |
| CA-0203 | «Notícies Parc Natural Cadí» → enllaç article | RF-0202 |
| CA-0204 | «Què veure a Besalú» → enllaç on anar | RF-0203 |
| CA-0205 | «Ruta a peu Pirineu» → enllaç `/rutes/` | RF-0204 |
| CA-0206 | «Cap de setmana Empordà» → enllaç agenda | RF-0210 |
| CA-0207 | «Arrossada Olvan» → enllaç experiència | RF-0206 |
| CA-0208 | Sense resultats → sense URLs inventades | RF-0215 |

### 9.3 Guies, admin, UAT global

| ID | Criteri |
|----|---------|
| CA-0301–0303 | Guies (com v1.0) |
| CA-0401–0405 | Admin PDF |
| UAT-2 | **Les 6 consultes** de catàleg des de MySQL |
| UAT-4 | ~30 converses; ≥80% routing correcte |

---

## 10. Matriu de traçabilitat

| CU | RF | CA | Responsable |
|----|-----|-----|-------------|
| CU-01 | RF-0201 | CA-0201, CA-0202 | Python |
| CU-02 | RF-0202 | CA-0203 | Python |
| CU-03 | RF-0203 | CA-0204 | Python |
| CU-04 | RF-0204 | CA-0205 | Python |
| CU-05 | RF-0205, RF-0210 | CA-0206 | Python |
| CU-06 | RF-0206 | CA-0207 | Python |
| CU-07 | RF-0301–0304 | CA-0301 | Python |
| CU-08 | RF-0214 | CA-0303 | Python |
| CU-09 | RF-0401–0407 | CA-0401 | Python + Ops |
| CU-10 | RF-0107 | CA-0105 | PHP + Python |
| — | RF-0101–0109 | CA-0101–0106 | PHP |

---

## 11. Glossari

Veure [dominio-femturisme-ca.md](dominio-femturisme-ca.md). Termes clau: **establiment**, **agenda**, **experiència**, **on anar**, **buscador**, **repositori**.

---

## 12. Referències

| Document | Ús |
|----------|-----|
| [dominio-femturisme-ca.md](dominio-femturisme-ca.md) | Model de negoci |
| [especificacio-tecnica-ca.md](especificacio-tecnica-ca.md) | Implementació |
| [sql-mapeo.md](sql-mapeo.md) | SQL per buscador |
