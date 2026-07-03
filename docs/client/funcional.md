# DISSENY FUNCIONAL

## Agent d'IA per a femturisme.cat

Aquest document descriu el funcionament funcional de l'agent d'intel·ligència artificial de femturisme.cat. Defineix com l'agent interpreta les consultes dels usuaris, com selecciona les fonts d'informació disponibles, com construeix les respostes i quins criteris segueix durant una conversa.

No descriu aspectes d'implementació tècnica, que es desenvolupen al document de [Disseny Tècnic](tecnic.md).

Documents relacionats: [requeriments.md](requeriments.md), [tecnic.md](tecnic.md), [dominio-femturisme-ca.md](dominio-femturisme-ca.md).

## Índex

- [1. Objectiu del document](#1-objectiu-del-document)
- [2. Visió funcional](#2-visió-funcional)
- [3. Principis de funcionament](#3-principis-de-funcionament)
- [4. Model funcional](#4-model-funcional)
- [5. Cicle d'una conversa](#5-cicle-duna-conversa)
- [6. Tipus de preguntes](#6-tipus-de-preguntes)
- [7. Context operatiu](#7-context-operatiu)
- [8. Fonts d'informació](#8-fonts-dinformació)
- [9. Gestió del context](#9-gestió-del-context)
- [10. Resolució de consultes](#10-resolució-de-consultes)
- [11. Gestió d'excepcions](#11-gestió-dexcepcions)
- [12. Model funcional de les Tools](#12-model-funcional-de-les-tools)
- [13. Priorització de les fonts](#13-priorització-de-les-fonts)
- [14. Gestió de la base de coneixement d'entitats](#14-gestió-de-la-base-de-coneixement-dentitats)
- [15. Administració de la documentació](#15-administració-de-la-documentació)
- [16. Selecció de Tools](#16-selecció-de-tools)
- [17. Construcció de la resposta](#17-construcció-de-la-resposta)
- [18. Evolució funcional](#18-evolució-funcional)
- [19. Fluxos funcionals](#19-fluxos-funcionals)

---

## 1. Objectiu del document

Aquest document descriu el funcionament funcional de l'agent d'intel·ligència artificial de femturisme.cat.

Defineix com l'agent interpreta les consultes dels usuaris, com selecciona les fonts d'informació disponibles, com construeix les respostes i quins criteris segueix durant una conversa.

No descriu aspectes d'implementació tècnica, que es desenvolupen al document de Disseny Tècnic.

---

## 2. Visió funcional

L'agent és un assistent virtual especialitzat en informació turística i coneixement del territori. El sistema es basa en un únic motor d'agent que pot funcionar en diferents contextos operatius, com ara l'assistent general de femturisme o l'assistent d'una entitat concreta.

La seva funció és ajudar l'usuari durant una conversa utilitzant la informació disponible al portal.

A diferència d'un cercador tradicional, l'agent no es limita a executar consultes. Per cada pregunta:

- interpreta la necessitat real de l'usuari;
- decideix quina informació necessita;
- consulta les fonts adequades;
- combina els resultats;
- genera una resposta natural.

L'objectiu no és retornar dades sinó ajudar l'usuari.

---

## 3. Principis de funcionament

L'agent basa el seu comportament en els següents principis.

### Comprensió

Abans de cercar informació intenta entendre què necessita realment l'usuari.

### Raonament

Decideix quines fonts consultar abans d'obtenir informació. No consulta totes les fonts indiscriminadament.

### Planificació

Quan una pregunta és complexa pot dividir-la en diversos passos interns.

**Exemple:** «Vull passar un cap de setmana amb nens al Ripollès.»

Pot convertir-ho internament en:

- activitats familiars;
- agenda del cap de setmana;
- allotjaments;
- rutes fàcils.

### Composició

Quan disposa dels resultats els integra en una única resposta coherent.

### Assistència

Si no troba exactament allò que demana l'usuari intenta oferir alternatives útils.

---

## 4. Model funcional

```text
Pregunta de l'usuari
        ↓
   Comprensió
        ↓
  Interpretació
        ↓
    Planificació
        ↓
 Selecció de fonts
        ↓
     Consultes
        ↓
     Raonament
        ↓
Construcció de resposta
        ↓
   Resposta final
```

Aquest serà pràcticament el cervell de l'agent.

---

## 5. Cicle d'una conversa

Cada torn de conversa seguirà el mateix procés funcional.

| Pas | Acció |
|-----|-------|
| **Pas 1** | Recepció del missatge. |
| **Pas 2** | Interpretació de la intenció. L'agent identifica: objectiu, ubicació, dates, tipus d'activitat, preferències, context existent. |
| **Pas 3** | Planificació. Decideix: quina informació necessita, quines fonts consultar, si calen diverses consultes, si necessita aclariments. |
| **Pas 4** | Obtenció de la informació. Consulta les fonts seleccionades. |
| **Pas 5** | Raonament. Relaciona els resultats, descarta informació poc útil, prioritza els continguts més rellevants. |
| **Pas 6** | Construcció de la resposta. Genera una resposta adaptada al nivell de detall que necessita l'usuari. |
| **Pas 7** | Actualització del context. Desa la informació necessària per continuar la conversa. |

---

## 6. Tipus de preguntes

L'agent haurà de ser capaç de gestionar diferents tipus de consultes.

| Tipus | Exemple |
|-------|---------|
| **Cerca directa** | Hotel a Vic. |
| **Recomanació** | On aniries aquest cap de setmana? |
| **Planificació** | Organitza'm un cap de setmana al Priorat. |
| **Comparació** | Què és millor per anar amb nens, la Garrotxa o el Ripollès? |
| **Informació** | Explica'm què és la Patum. |
| **Coneixement** | A quin any es va construir el castell de Berga? Qui va dissenyar la façana de...? Quin és l'origen de la Patum? |
| **Seguiment de conversa** | I què més puc fer? |
| **Preguntes obertes** | Sorprèn-me. |

---

## 7. Context operatiu

Inicialment el motor podrà treballar en dos contextos operatius:

### Mode femturisme

- informació del portal (catàleg MySQL);
- eines de catàleg disponibles per al portal;
- identitat de femturisme;
- **Fase 1:** sense consulta documental (RAG);
- **Fase 2:** RAG només si algun element retornat per una Tool de catàleg porta `entity_id` associada — en la resta de casos, només catàleg.

### Mode entitat

- informació exclusiva de l'entitat;
- documentació pròpia;
- configuració pròpia;
- identitat pròpia.

El context operatiu determinarà:

- Tools disponibles;
- fonts consultables;
- configuració;
- restriccions d'accés.

---

## 8. Fonts d'informació

L'agent obté la informació a partir de diferents fonts de dades especialitzades. Cada font proporciona informació sobre un àmbit concret del portal.

L'usuari interactua amb un únic assistent, però internament aquest és capaç de consultar una o diverses fonts segons la naturalesa de cada pregunta.

La incorporació de noves fonts d'informació no haurà de modificar el comportament general de l'agent.

### 8.1 Catàleg de continguts

El catàleg de femturisme constitueix la principal font d'informació de l'agent.

Aquest catàleg inclou, entre d'altres:

- establiments turístics;
- destinacions;
- agenda d'activitats;
- experiències;
- rutes;
- articles i continguts editorials.

L'agent seleccionarà automàticament quins tipus de contingut són necessaris per respondre cada consulta.

### 8.2 Documents indexats

L'agent podrà consultar documentació addicional incorporada al sistema mitjançant processos d'indexació.

Inicialment aquesta documentació correspondrà principalment a documentació associada a una entitat.

**Exemples:**

- guies turístiques;
- museus;
- monuments;
- programes de festes;
- patrimoni;
- documentació institucional;
- qualsevol altra informació aportada per l'entitat;
- fulletons turístics;
- documentació informativa.

Quan la resposta es basi en aquesta documentació, l'agent n'indicarà l'origen.

### 8.3 Fonts futures

L'arquitectura funcional es dissenya per permetre la incorporació de noves fonts d'informació en futures versions.

Entre d'altres:

- portals oficials;
- APIs externes;
- dades obertes;
- nous repositoris documentals;
- altres serveis relacionats amb el turisme.

La incorporació d'aquestes fonts no haurà de modificar la manera com interactua l'usuari amb l'agent.

### 8.4 Base de coneixement d'entitats

Cada entitat podrà disposar d'una base de coneixement pròpia formada per documentació indexada.

L'entitat podrà ser, entre d'altres:

- un ajuntament;
- una població;
- un museu;
- una fira;
- un establiment;
- una oficina de turisme;
- qualsevol altre client.

Quan l'agent treballi en el context d'una entitat (**mode entitat**), prioritzarà aquesta documentació.

Quan treballi en **mode femturisme**:

- **Fase 1:** no consultarà cap base documental; només el catàleg MySQL.
- **Fase 2:** consultarà RAG **únicament** si algun element de la resposta de catàleg inclou `entity_id`. Si cap en té, no s'activa RAG.

Aquest comportament reflecteix que, al llançament, gairebé cap fitxa del portal tindrà entitat associada (només un parell de proves inicials). El RAG no és una font transversal del portal femturisme.

---

## 9. Gestió del context

L'agent mantindrà un context de conversa durant tota la sessió amb l'objectiu d'evitar que l'usuari hagi de repetir informació.

El context podrà incloure, entre altres:

- destinació seleccionada;
- dates;
- perfil dels visitants;
- preferències expressades;
- activitats ja recomanades;
- preguntes anteriors.

### 9.1 Reutilització del context

Quan una pregunta posterior pugui resoldre's utilitzant informació ja disponible al context, l'agent la reutilitzarà automàticament.

**Exemple:**

> **Usuari:** Vull passar el cap de setmana a la Vall d'Aran.
>
> **Usuari:** Hi ha rutes fàcils?

L'agent entendrà que la consulta continua referint-se a la Vall d'Aran.

### 9.2 Actualització del context

Després de cada resposta, l'agent actualitzarà la informació rellevant del context per facilitar la continuïtat de la conversa.

### 9.3 Reinici del context

L'usuari podrà iniciar una nova conversa en qualsevol moment.

En aquest cas, el context acumulat durant la sessió anterior deixarà d'utilitzar-se.

---

## 10. Resolució de consultes

Aquest apartat és el que descriu realment com treballa l'agent.

Per respondre una consulta, l'agent seguirà el següent procés funcional:

1. **Comprendre la petició** — Analitzarà el text introduït per l'usuari.

2. **Identificar la intenció** — Determinarà què necessita realment l'usuari.

3. **Obtenir els paràmetres necessaris** — Per exemple: municipi, comarca, dates, tipus d'activitat, perfil dels visitants, altres condicionants. Quan alguna informació imprescindible no estigui disponible, podrà sol·licitar aclariments.

4. **Seleccionar les fonts d'informació disponibles segons el context operatiu** — Determinarà quines fonts són necessàries per construir la resposta. Es podran consultar una o diverses fonts dins del mateix procés.

5. **Analitzar els resultats** — L'agent valorarà la rellevància de la informació obtinguda. Quan sigui necessari: eliminarà informació redundant, priorititzarà els continguts més útils, detectarà possibles mancances.

6. **Construir la resposta** — Finalment generarà una resposta coherent, contextualitzada i orientada a ajudar l'usuari. Quan sigui possible, incorporarà enllaços als continguts corresponents de femturisme.cat.

---

## 11. Gestió d'excepcions

Quan l'agent no pugui proporcionar una resposta completa, aplicarà diferents estratègies segons la situació.

### Sense resultats

Intentarà ampliar la cerca abans d'indicar que no hi ha informació disponible. Per exemple:

- ampliar la zona geogràfica;
- suggerir categories similars;
- proposar altres dates.

### Informació insuficient

Quan la consulta sigui massa ambigua, demanarà únicament els aclariments imprescindibles.

### Error d'accés a les dades

Quan alguna font d'informació no estigui disponible, informarà l'usuari de forma clara i, sempre que sigui possible, continuarà utilitzant la resta de fonts disponibles.

### Informació parcial

Quan només es disposi d'una part de la informació necessària, l'agent construirà la millor resposta possible indicant les limitacions.

---

## 12. Model funcional de les Tools

L'agent disposa d'un conjunt de Tools que li permeten accedir a diferents fonts d'informació i executar accions específiques.

Una Tool representa una capacitat funcional de l'agent. L'agent decidirà de forma autònoma quina o quines Tools utilitzar per respondre cada consulta.

L'usuari no interactuarà directament amb les Tools ni haurà de conèixer la seva existència. Una mateixa resposta podrà requerir la utilització d'una o diverses Tools.

### 12.1 Característiques generals

Totes les Tools comparteixen els següents principis:

- tenen una responsabilitat concreta;
- només retornen informació estructurada;
- no generen text per a l'usuari;
- poden ser combinades entre elles;
- poden evolucionar independentment de la resta del sistema.

La construcció de la resposta correspon sempre a l'agent.

### 12.2 Classificació de les Tools

Les Tools es poden classificar segons la seva finalitat.

#### Tools de consulta

Permeten obtenir informació de les diferents fonts disponibles. Per exemple:

- agenda;
- establiments;
- destinacions;
- rutes;
- experiències;
- articles;
- base de coneixement d'entitats.

#### Tools documentals

Permeten consultar informació extreta de documents associats a una població o a un context concret.

Aquesta informació complementa el contingut del portal i, quan sigui rellevant, tindrà prioritat en les respostes relacionades amb aquella localitat.

#### Tools de context

Permeten obtenir informació relacionada amb el context de la conversa o de l'entorn on està funcionant l'agent.

**Exemples:**

- població actual;
- context del portal;
- idioma;
- pàgina on es troba l'usuari.

#### Tools futures

L'arquitectura permetrà incorporar noves Tools sense modificar el comportament general de l'agent.

---

## 13. Priorització de les fonts

Quan una consulta pugui respondre's amb diverses fonts, l'agent seguirà un ordre de prioritat.

Aquest ordre podrà variar segons el context operatiu.

**Mode entitat:**

1. Base de coneixement de l'entitat activa.

**Mode femturisme:**

1. Continguts estructurats de femturisme (catàleg MySQL) — font principal i, a Fase 1, l'única.
2. Base de coneixement d'entitat — **només Fase 2**, i només si algun element retornat porta `entity_id`.

No existeix «RAG general» del portal en mode femturisme: sense `entity_id` a la resposta de catàleg, no hi ha consulta documental.

L'agent podrà combinar catàleg + RAG d'entitat quan, i només quan, la condició anterior es compleixi.

---

## 14. Gestió de la base de coneixement d'entitats

Aquest apartat és nou i crec que serà una de les funcionalitats diferencials del projecte.

Cada entitat podrà disposar d'un conjunt de documents propis que complementaran la informació publicada a femturisme.cat.

Aquests documents podran incloure informació específica difícil de representar mitjançant fitxes estructurades. Per exemple:

- museus;
- monuments;
- espais naturals;
- festes locals;
- patrimoni;
- serveis municipals;
- equipaments;
- informació turística.

### Funcionament

Quan una consulta faci referència a una població concreta, l'agent haurà de valorar si existeix documentació associada.

Si aquesta informació és rellevant per respondre la pregunta, haurà de prioritzar-la respecte al contingut general del portal.

**Exemple:**

> **Usuari:** Què podem veure al Museu de Bagà?

L'agent podrà construir la resposta utilitzant principalment la documentació específica del museu, complementant-la amb la informació existent a femturisme.cat quan sigui necessari.

---

## 15. Administració de la documentació

El sistema disposarà d'un gestor documental integrat al backend de femturisme.

Aquest gestor permetrà administrar la documentació utilitzada per l'agent.

**Les funcionalitats mínimes seran:**

- pujar nous documents;
- associar-los a una entitat;
- crear entitats;
- editar entitats;
- eliminar entitats;
- consultar el llistat de documents disponibles;
- conèixer el seu estat de processament;
- tornar a processar un document quan sigui necessari;
- eliminar documents.

L'objectiu és que l'equip editorial pugui mantenir actualitzada la documentació utilitzada per l'agent sense necessitat d'intervenció tècnica.

---

## 16. Selecció de Tools

L'agent seleccionarà de manera autònoma les Tools necessàries per respondre cada consulta.

La selecció dependrà de:

- la intenció de l'usuari;
- el context de la conversa;
- el context operatiu;
- la informació ja coneguda;
- les fonts disponibles.

L'objectiu serà obtenir la informació mínima necessària per construir una resposta útil, evitant consultes innecessàries.

### 16.1 Utilització d'una única Tool

Quan la pregunta pugui respondre's mitjançant una única font d'informació, l'agent utilitzarà exclusivament la Tool corresponent.

**Exemple:** «Quan és la Patum?»

Només serà necessari consultar la informació corresponent a l'esdeveniment.

### 16.2 Utilització de diverses Tools

Quan la consulta sigui més complexa, l'agent podrà combinar diverses Tools.

**Exemple:** «Vull passar un cap de setmana al Berguedà.»

L'agent podrà consultar, entre d'altres:

- agenda;
- allotjaments;
- experiències;
- rutes;
- documentació específica del territori.

La resposta final integrarà tota la informació obtinguda.

### 16.3 Consultes condicionals

La selecció de determinades Tools podrà dependre dels resultats obtinguts en consultes prèvies.

**Exemple (mode femturisme, Fase 2):**

1. Executar Tool de catàleg (p. ex. establiments, destinacions, agenda).
2. Revisar si **algun** element de `results[]` inclou `entity_id`.
3. Si **cap** en té → respondre només amb catàleg; **no** invocar RAG.
4. Si **n'hi ha** → consultar la base de coneixement d'aquella entitat i combinar amb la fitxa.

En la pràctica, la majoria de consultes (≈99,9 %) no activaran aquest flux fins que l'equip comercial ampliï les associacions portal ↔ entitat.

### 16.4 Minimització de consultes

L'agent procurarà evitar consultes redundants.

Quan la informació ja estigui disponible al context de la conversa, no serà necessari tornar-la a obtenir.

---

## 17. Construcció de la resposta

Una vegada obtinguda tota la informació necessària, l'agent construirà una resposta única per a l'usuari.

La resposta haurà de:

- respondre directament a la pregunta;
- presentar la informació de forma clara;
- evitar repeticions;
- justificar les recomanacions;
- indicar les limitacions quan sigui necessari;
- incorporar enllaços rellevants cap a femturisme.cat.

### 17.1 Adaptació al nivell de detall

L'agent adaptarà la quantitat d'informació proporcionada segons la consulta.

| Tipus de pregunta | Exemple | Resposta |
|-------------------|---------|----------|
| Simple | «On és Rupit?» | Breu. |
| Oberta | «Organitza'm un cap de setmana a Rupit.» | Molt més desenvolupada. |

### 17.2 Recomanacions

Quan existeixin diverses opcions vàlides, l'agent explicarà els motius pels quals proposa unes opcions determinades.

Les recomanacions es basaran en:

- el context de la conversa;
- la informació disponible;
- els criteris indicats per l'usuari.

L'agent evitarà presentar les recomanacions com a opinions personals.

### 17.3 Transparència

Quan una resposta es basi en la base de coneixement de l'entitat, l'agent podrà indicar-ho de manera natural dins la resposta.

**Exemple:** «Segons la informació disponible sobre el Museu de Bagà...»

Aquest tipus de referència ajuda a donar confiança a l'usuari i aporta transparència sobre l'origen de la informació.

---

## 18. Evolució funcional

El disseny funcional de l'agent s'ha concebut per facilitar la incorporació de noves capacitats sense modificar-ne el funcionament general.

Entre les possibles evolucions es contemplen:

- noves Tools;
- noves fonts d'informació;
- nous contextos operatius;
- nous canals d'interacció;
- nous tipus de documentació;
- noves funcionalitats de planificació i recomanació.

L'objectiu és garantir que el sistema pugui créixer de manera modular mantenint una experiència d'usuari coherent.

---

## 19. Fluxos funcionals

Documentació de diversos fluxos complets.

### Flux 1 — Consulta simple

```text
Usuari
  │
  ▼
Comprensió
  │
  ▼
1 Tool
  │
  ▼
Resposta
```

### Flux 2 — Consulta complexa

```text
Usuari
  │
  ▼
Comprensió
  │
  ▼
Planificació
  │
  ▼
Agenda ── Hotels ── Experiències ── Documents
  │
  ▼
Raonament
  │
  ▼
Resposta única
```

### Flux 3 — Agent municipal

```text
Usuari
  │
  ▼
Determinar context operatiu
  │
  ├─────────────────────┐
  ▼                       ▼
Mode femturisme      Mode entitat
  │                       │
  └───────────┬───────────┘
              ▼
Seleccionar fonts disponibles
              │
              ▼
           Resposta
```
