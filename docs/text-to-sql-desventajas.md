# Text-to-SQL vs tools parametrizades — Desavantatges de deixar que el LLM escrigui SQL lliure

Document de referència basat en l'[Annex D del pla d'integració](plan-integracion-ca.md#anexo-d). Respon: *per què el backend no deixa el LLM escriure SQL lliure contra MySQL? No simplificaria l'agent?*

---

## 1. La pregunta

En un xat amb tool use, el LLM pot rebre una tool genèrica:

```json
{
  "name": "execute_sql",
  "parameters": {
    "query": "SELECT titol, slug FROM experiencies WHERE ..."
  }
}
```

El backend executaria aquesta cadena contra MySQL i retornaria les files al LLM. **Això és possible.** Molts prototips i demos d'«agent + base de dades» funcionen exactament així.

La pregunta rellevant no és «es pot?» sinó «quina complexitat eliminem i quina complexitat movem a un altre lloc?».

---

## 2. Dues arquitectures comparades

### A) Tools parametritzades (decisió del pla)

```
Usuari (NL) → LLM tria tool + params → Python executa SQL fixa → JSON normalitzat → LLM respon
```

- El LLM ve: **SCHEMA de 4–5 tools** (nom, descripció, paràmetres).
- El LLM **no ve**: schema MySQL, noms de taules, SQL.
- El backend controla: taules, JOINs, regles de negoci, `LIMIT`, format de sortida.

### B) Text-to-SQL al vol (alternativa descartada per a v1)

```
Usuari (NL) → LLM genera SELECT → Python executa tal qual → files crues → LLM respon
```

- El LLM ve: **schema complet** (o un resum) + instruccions de generar SQL.
- El LLM **escriu**: la query en cada torn.
- El backend ha de: validar, restringir, limitar, normalitzar — o confiar cegament.

---

## 3. Què sembla estalviar text-to-SQL

| El que no caldria (en principi) | Detall |
|---------------------------------|--------|
| 4 repositoris Python | Una sola tool `execute_sql` |
| `sql-mapeo.md` per tool | El LLM «descobreix» taules al vol |
| Ampliar paràmetres SCHEMA | Qualsevol filtre seria SQL ad hoc |
| Fase 2–3 llarga | MVP més ràpid per provar connexió BD |

Per a un **experiment intern** o una **demo**, això pot ser cert.

---

## 4. Desavantatges principals: la complexitat no desapareix

Muntar text-to-SQL en **producció** davant usuaris reals exigeix capes que, amb tools parametritzades, ja estan resoltes en codi:

| Capa | Tools parametritzades | Text-to-SQL en producció |
|------|----------------------|---------------------------|
| Conèixer l'schema | L'estudia el dev a la Fase 2 | Cal **injectar l'schema al LLM** en cada torn (milers de tokens) o resumir-lo malament |
| Regles de negoci (`publicat = 1`, dates vigents, idioma…) | Van a la SQL fixa del repo | El LLM ha d'**inferir-les** o les omet |
| Límit de files | `LIMIT 20` en codi | Validador que **rebutgi o reescrigui** queries sense `LIMIT` |
| Taules permeses | Només les del repositori | Parser + allowlist: **només `SELECT`**, només taules X/Y/Z |
| Format al xat | JSON estable (Annex B del pla) | Normalitzador post-query: files → cards amb `title`, `url`, `image` |
| Tests automatitzats | Casos fixos a CI (`destination=Berguedà` → N files) | La SQL **canvia cada torn** i amb cada versió del model |
| Depuració | «La query d'experiences filtra malament el JOIN X» | «Claude va generar una altra SQL ahir que funcionava» |
| Cost/latència LLM | Prompt petit (només SCHEMA de tools) | Schema gran + SQL generada + reintents si falla |

**Conclusió:** no elimines la Fase 2; la converteixes en «posar tot l'schema legacy al prompt i confiar que el model l'interpreti bé en cada pregunta».

---

## 5. Per què MySQL read-only no resol el problema

L'usuari `agent_read` sense permisos d'escriptura **evita esborrar o modificar dades**, però **no limita què es pot llegir** ni **quant costa llegir-ho**.

Exemples de queries que un LLM pot generar sense mala intenció:

```sql
-- Taules sensibles (si existeixen i l'usuari té SELECT)
SELECT email, password_hash FROM users LIMIT 1000;

-- Cartesian product / query costosa
SELECT * FROM orders o
JOIN order_items i ON ...
JOIN products p ON ...
JOIN categories c ON ...;

-- Columnes inventades (error en runtime)
SELECT titol, allows_dogs FROM experiencies WHERE zona = 'Berguedà';
-- → Unknown column 'allows_dogs'
```

Els errors habituals no són atacs; són **al·lucinacions de columnes**, **JOINs incorrectes** i **oblidar filtres de negoci** en schemas legacy amb noms críptics (`tbl_cnt`, `rel_ubicacio_2`, etc.).

---

## 6. El problema concret de femturisme

Hi ha tres capes que l'agent ha d'encertar alhora:

| Capa | Contingut | Amb text-to-SQL |
|------|-----------|-----------------|
| **1. Schema legacy** | Taules, relacions, noms no obvis | El LLM ha d'encertar JOINs en cada torn |
| **2. Regles de negoci** | Publicat, vigent, idioma — sovint a PHP, no a FK | El LLM no les coneix llevat que estiguin documentades al prompt |
| **3. Contracte de producte** | Cards amb URL canònica, imatge, títol | Les files SQL crues no coincideixen amb el que el xat ha de mostrar |

Amb **tools parametritzades**, el LLM només resol la capa d'**intenció** («què buscar»). Les capes 1–3 les garanteix el backend en codi revisat.

---

## 7. Quina flexibilitat sí aporta el LLM (sense SQL lliure)

El LLM ja aporta la flexibilitat que l'usuari percep:

| Capacitat | Exemple |
|-----------|---------|
| Triar tool(s) | Agenda + guia PDF en la mateixa pregunta |
| Inferir paràmetres | «Berguedà en família» → `destination`, `category` |
| Criteris tous | «Amb gossos» → filtra sobre `description` del JSON |
| Combinar resultats | Barreja catàleg MySQL + chunks RAG a la resposta |
| Idioma i to | Respon en català/castellà segons l'usuari |

Aquesta flexibilitat **no requereix** que el LLM escrigui SQL.

---

## 8. Comparació d'esforç total (v1, 4 dominis de catàleg)

| Dimensió | Tools parametritzades | Text-to-SQL al vol |
|----------|----------------------|---------------------|
| Complexitat upfront | Alta (Fase 2–3, una vegada) | Baixa (tool genèrica ràpida) |
| Complexitat ongoing | Baixa (canvis en PR) | **Alta** (validadors, prompt schema, debugging) |
| Risc en producció | Baix | **Mitjà–alt** |
| Predictibilitat | Alta | **Baixa** |
| Testabilitat a CI | Alta | **Baixa** |
| Superfície de dades exposada | Mínima (taules de catàleg) | **Tota taula amb `SELECT` permès** |

Per a **quatre dominis acotats** (ofertes, allotjaments, agenda, rutes), parametritzar sol implicar **menys treball total** que muntar un sandbox SQL robust.

---

## 9. Què caldria implementar igual amb text-to-SQL

Si es triés text-to-SQL per a producció, el backend necessitaria com a mínim:

1. **Injecció de schema** — `docs/schema.sql` o subconjunt en cada request (cost tokens).
2. **Parser SQL** — rebutjar `INSERT`, `UPDATE`, `DELETE`, `DROP`, subqueries perilloses, múltiples statements.
3. **Allowlist de taules** — només taules de catàleg; rebutjar la resta.
4. **`LIMIT` obligatori** — injectar o rebutjar si falta (p. ex. màx. 50 files).
5. **Timeout de query** — p. ex. 2 s; matar queries lentes.
6. **Normalitzador de sortida** — files → JSON Annex B (URLs, imatges, slugs).
7. **Logging de queries generades** — per auditar què va executar el LLM.
8. **Reintents** — quan la SQL falla per columna inexistent (comú).

Això és comparable en esforç a implementar 4 repositoris, però **més fràgil** en runtime.

---

## 10. Alternatives intermèdies

| Alternativa | Descripció | Quan té sentit |
|-------------|------------|----------------|
| **Vistes SQL a MySQL** | `CREATE VIEW v_experiences_public AS …`; el LLM només consulta vistes | Redueix taules sensibles; no elimina al·lucinacions ni JSON inestable |
| **Text-to-SQL només a staging** | Tool interna per a devs que exploren l'schema | Fase 2 d'exploració; sense tràfic d'usuaris |
| **Híbrid post-v1** | Tools parametritzades + cinena tool molt restringida per a casos rars | Només si apareix demanda real no coberta per les 4 tools |
| **Schema-on-read al prompt** | Resum manual de 20 taules clau al system prompt | Compromís fràgil; requereix manteniment manual |

---

## 11. Decisió formal (v1)

| Aspecte | Decisió |
|---------|---------|
| **Mecanisme catàleg** | Tools parametritzades: `search_experiences`, `search_accommodations`, `search_events`, `search_routes` |
| **SQL** | Fixa a `app/db/repositories/*.py`; documentada a `sql-mapeo.md` |
| **Visibilitat LLM** | SCHEMA de tools + JSON de resultats; **sense** schema MySQL ni SQL |
| **Text-to-SQL** | **No** al xat de producció v1 |
| **Revisió** | Després de v1 en producció, si >20% de preguntes de catàleg no es resolen amb les 4 tools, avaluar ampliar paràmetres o vistes SQL abans que text-to-SQL |

---

## 12. Resposta llista per compartir amb el client

> «Per què no deixem que Claude escrigui la query?»
>
> Perquè **sí es pot**, però **no redueix la complexitat total** en un entorn de producció amb schema legacy: desplaça el treball d'«escriure quatre queries ben fetes» a «validar SQL arbitrària, injectar schema, normalitzar resultats i depurar queries trencades en cada conversa». Per a un catàleg turístic amb respostes en cards i dades sensibles a la mateixa BD, les tools parametritzades ofereixen **menys sorpreses**, **tests reproduïbles** i **menor superfície d'exposició de dades**. El LLM segueix sent flexible en *què* buscar i *com* respondre; el que fixem en codi és *com* accedir a MySQL de forma segura i estable.

---

## Referències

- [Pla d'integració (català)](plan-integracion-ca.md) — Annex D
- [Mapeig SQL per tool](sql-mapeo.md)
- [Fase 3 — Tools MySQL](fase-3-tools-mysql-ca.md)
