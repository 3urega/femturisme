Document 01
Presa de requeriments
Agent d’IA per a femturisme.cat
Estat del document
Camp
Valor
Projecte
Agent d’IA per a femturisme.cat
Document
Presa de requeriments
Versió
0.1
Data
2026
Estat
Esborrany inicial
Destinataris
Direcció, equip femturisme, consultora, equip tècnic


1. Context del projecte
femturisme.cat és un portal turístic especialitzat en la difusió de continguts turístics de Catalunya i Andorra. El portal disposa d’un catàleg ampli d’informació format per continguts editorials, fitxes de destinacions, agenda d’esdeveniments, rutes, establiments, experiències i altres recursos vinculats al territori.
Actualment, aquesta informació es consulta principalment mitjançant navegació web tradicional: menús, cercadors, filtres, fitxes i pàgines de contingut. El projecte planteja incorporar un agent d’intel·ligència artificial que permeti als usuaris interactuar amb femturisme.cat mitjançant llenguatge natural.
L’agent ha de poder entendre preguntes dels visitants, consultar les fonts d’informació disponibles i generar respostes útils, estructurades i amb enllaços cap a les pàgines corresponents de femturisme.cat.
El projecte no es planteja únicament com un assistent conversacional per a femturisme.cat, sinó com una plataforma reutilitzable basada en un únic motor d'agent d'intel·ligència artificial. Aquest motor podrà actuar tant com a assistent general de femturisme com com a assistent especialitzat d'una entitat concreta, segons el context operatiu amb què sigui invocat. 

2. Objectiu general
L'objectiu del projecte és definir, desenvolupar i integrar una plataforma d'agents d'intel·ligència artificial especialitzada en informació turística i coneixement del territori.
La primera implementació serà l'assistent general de femturisme.cat, capaç d'ajudar els usuaris mitjançant llenguatge natural consultant les fonts d'informació autoritzades.
La plataforma es dissenyarà perquè el mateix motor pugui funcionar també com a assistent d'una entitat concreta, limitant les consultes exclusivament a la informació autoritzada per aquella entitat.
L’agent haurà de:
entendre la intenció de l’usuari;
identificar les fonts d’informació més adequades;
consultar dades controlades de femturisme.cat;
generar respostes clares i útils;
incloure enllaços cap al portal quan hi hagi resultats rellevants;
evitar inventar informació no disponible;
funcionar com a punt d’entrada conversacional al contingut de femturisme.

3. Objectius específics
Els objectius específics del projecte són:
Crear una interfície conversacional integrada a femturisme.cat.
Permetre consultes en llenguatge natural sobre el catàleg turístic del portal.
Facilitar la descoberta de continguts existents que actualment poden quedar amagats dins l’estructura web.
Incrementar el tràfic cap a fitxes i pàgines internes de femturisme.cat.
Millorar l’experiència de l’usuari en consultes complexes, com ara:
“Què puc fer aquest cap de setmana al Berguedà?”
“On puc anar amb nens a la Cerdanya?”
“Rutes fàcils a prop de Besalú”
“On dormir i què visitar a l’Empordà?”
Disposar d'una arquitectura preparada per ampliar les capacitats de l'agent i reutilitzar el mateix motor en diferents contextos operatius. 
Evitar que l’agent faci consultes lliures i no controlades sobre la base de dades.
Permetre que un únic motor d'agent pugui actuar tant com a assistent general de femturisme com com a assistent d'una entitat. 
Facilitar la incorporació de bases de coneixement documentals independents associades a entitats. 

4. Fases del projecte
Fase 1
Assistent general de femturisme.
Consulta de la BBDD.
Consulta del RAG general.
Preguntes de recomanació turística.
Preguntes de coneixement sobre el territori.
Fase 2
Gestor d'entitats.
Gestió documental per entitat.
Assistent d'entitats.
Integració entre femturisme i les entitats.
Associació d'una entity_id als elements del portal.
Inclòs en l’abast inicial
Xat o interfície conversacional integrada a femturisme.cat.
Xat o interfície conversacional pròpia per Entitat
Consultes sobre contingut del catàleg de femturisme.
Consultes sobre guies o documents PDF indexats.
Respostes en llenguatge natural.
Enllaços cap a pàgines internes de femturisme.cat.
Ús de fonts d’informació controlades.
Panell intern per gestionar guies PDF.
Funcionament inicial en català, castellà, anglès i francès.
Registre bàsic d’activitat i errors.
Fora de l'abast inicial
Edició de continguts del CMS des del xat.
Creació automàtica de fitxes o articles.
Accés lliure a SQL generat per la IA.
Compra o reserva directa.
Integració amb passarel·les de pagament.
Ús de geolocalització GPS en temps real.
Publicació automàtica a xarxes socials.
Integració amb canals externs (WhatsApp, Telegram, Instagram, etc.).
Recomanacions personalitzades basades en perfils persistents d'usuari.
Consulta de fonts d'informació externes a femturisme.cat.
Nota: L'arquitectura de l'agent s'ha de dissenyar de manera modular per permetre incorporar, en futures versions, noves fonts d'informació externes (APIs, portals oficials, dades obertes o altres serveis), mantenint sempre la separació entre les fonts internes i les fonts externes.
5. Actors del sistema
El sistema identifica els següents actors que interactuen amb l'agent d'intel·ligència artificial:
Actor
Descripció
Visitant
Usuari final que interactua amb l'agent mitjançant llenguatge natural per obtenir informació turística.
Administrador de continguts
Personal de femturisme responsable de mantenir les fonts d'informació addicionals (per exemple, guies municipals).
Administrador tècnic
Responsable del desplegament, configuració, monitorització i manteniment tècnic del sistema.
Sistema femturisme.cat
Portal web que integra l'agent i proporciona accés al catàleg de continguts.
Agent d'IA
Component responsable d'interpretar les preguntes, consultar les fonts d'informació disponibles i generar les respostes.


6. Capacitats de l'agent
L'agent haurà de comportar-se com un assistent turístic virtual especialitzat en el contingut de femturisme.cat.
Les seves principals capacitats seran:
C1. Comprensió del llenguatge natural
L'agent haurà d'entendre preguntes formulades de manera natural, sense necessitat que l'usuari utilitzi paraules clau o filtres específics.
Exemples:
"Què puc fer aquest cap de setmana?"
"Busco un hotel romàntic."
"Anem amb nens."
"Vull passar tres dies al Priorat."

C2. Interpretació de la intenció
L'agent haurà d'identificar què està demanant realment l'usuari.
Per exemple, distingir entre:
una cerca concreta;
una recomanació;
una planificació;
una consulta informativa.

C3. Raonament
L'agent haurà de respondre tant consultes orientades a la recomanació turística com preguntes de coneixement relacionades amb el patrimoni, la història, la cultura, la natura i qualsevol altra informació disponible a les fonts autoritzades. 
Aquest procés podrà implicar:
dividir una pregunta en diverses consultes;
combinar els resultats obtinguts;
descartar informació irrellevant;
elaborar una resposta adaptada a la petició.
L'agent no actuarà com un simple cercador sinó com un sistema capaç de raonar sobre la informació disponible.

C4. Consulta de fonts d'informació
L'agent haurà de consultar una o diverses fonts internes segons la necessitat de cada conversa.
Les fonts podran incloure dades estructurades del portal i bases documentals associades a una entitat. El conjunt de fonts disponibles dependrà del context operatiu de l'agent. 

C5. Context conversacional
L'agent haurà de mantenir el context durant la conversa.
Exemple:
Usuari:
Vull anar al Berguedà.
Després:
I on puc dormir allà?
L'agent haurà d'entendre que "allà" continua sent el Berguedà.

C6. Recomanació
L'agent haurà de ser capaç de generar recomanacions basades en la informació disponible.
Aquestes recomanacions podran tenir en compte, entre altres:
destinació;
dates;
tipus d'activitat;
perfil del visitant;
preferències indicades durant la conversa.

C7. Transparència
Quan no disposi d'informació suficient, l'agent haurà d'indicar-ho de manera explícita i evitar inventar dades.

C8. Evolució
L'arquitectura funcional haurà de permetre incorporar noves Tools, noves fonts d'informació i noves entitats sense modificar el comportament general del motor de l'agent. 

7. Principis de funcionament
L'agent haurà de respectar els següents principis:
P1. Prioritzar les fonts pròpies
Les respostes es construiran utilitzant preferentment la informació disponible a femturisme.cat.

P2. Informació fiable
Només es retornarà informació procedent de fonts conegudes i controlades.

P3. No inventar informació
En absència d'informació suficient, l'agent ho indicarà a l'usuari.

P4. Orientació al visitant
Les respostes hauran de ser útils, naturals i orientades a ajudar el visitant.

P5. Promoció del contingut del portal
Sempre que sigui possible, l'agent facilitarà l'accés a les pàgines corresponents de femturisme.cat.

P6. Evolució futura
La primera versió treballarà exclusivament amb fonts internes.
No obstant això, el sistema haurà de permetre incorporar, en futures versions, fonts externes mantenint clarament diferenciada la procedència de la informació.

8. Filosofia de l'agent
L'agent d'IA de femturisme.cat es concep com un assistent turístic digital, no com un simple sistema de cerca.
La seva funció principal és ajudar l'usuari a trobar la millor resposta possible utilitzant la informació disponible, adaptant-se al context de la conversa i proposant alternatives quan sigui necessari.
Per assolir aquest objectiu, l'agent haurà d'aplicar els següents criteris:
Assistència activa
L'agent no s'ha de limitar a executar una consulta i retornar els resultats obtinguts.
Quan la informació disponible sigui insuficient o no existeixin coincidències exactes, haurà d'intentar ajudar l'usuari proposant alternatives raonables.
Per exemple:
ampliar l'àrea geogràfica de cerca;
suggerir activitats similars;
recomanar altres dates;
proposar categories relacionades;
combinar diferents tipus de contingut.

Raonament abans de respondre
L'agent haurà d'analitzar la petició abans de decidir quines fonts consultar.
Quan sigui necessari, podrà dividir una mateixa pregunta en diverses consultes independents i combinar-ne els resultats per construir una resposta única.

Adaptació al context
L'agent haurà de tenir en compte la informació aportada durant la conversa.
No serà necessari repetir dades que ja hagin estat indicades prèviament per l'usuari.

Resposta orientada a ajudar
L'objectiu principal serà facilitar que l'usuari pugui planificar la seva visita o trobar allò que necessita.
Per aquest motiu, les respostes prioritzaran la utilitat per sobre de la simple enumeració de resultats.
Transparència
Quan una resposta es basi en informació parcial o no sigui possible satisfer exactament la petició, l'agent ho comunicarà de forma clara i oferirà alternatives quan sigui possible.


Assistent de coneixement
L'agent no només recomanarà activitats o recursos turístics, sinó que també haurà de respondre preguntes de coneixement utilitzant la informació disponible a les fonts autoritzades.
Exemples:
Quan es va construir el castell de Berga?
Qui va dissenyar...?
Quins edificis van construir els deixebles de Gaudí?

9. Requeriments funcionals
RF-01. Conversa en llenguatge natural
L'agent haurà de permetre als usuaris interactuar mitjançant llenguatge natural, sense necessitat de conèixer l'estructura del portal ni utilitzar paraules clau específiques.
Haurà de comprendre preguntes formulades de manera espontània, encara que estiguin incompletes o utilitzin expressions col·loquials.
Exemples:
"Què puc fer aquest cap de setmana?"
"Busco alguna cosa tranquil·la."
"Anem amb nens."
"No volem caminar gaire."

RF-02. Comprensió de la intenció
L'agent haurà d'identificar la intenció real de l'usuari abans d'iniciar qualsevol consulta.
Entre d'altres, haurà de distingir:
cerca d'informació;
cerca d'activitats;
cerca d'establiments;
planificació d'una visita;
recomanació;
consulta sobre una destinació;
consulta sobre una data concreta;
comparació entre opcions.

RF-03. Consulta de fonts d'informació
L'agent haurà de consultar les fonts d'informació internes necessàries per construir cada resposta.
Podrà utilitzar una o diverses fonts dins d'un mateix torn de conversa.
La selecció de les fonts serà transparent per a l'usuari.
Les fonts consultades dependran del context operatiu amb què s'executi el motor de l'agent.

RF-04. Combinació d'informació
Quan una resposta requereixi informació procedent de diverses fonts, l'agent haurà de combinar-la en una única resposta coherent.
Per exemple:
"Vull passar un cap de setmana a la Garrotxa."
L'agent podrà combinar:
activitats;
agenda;
allotjaments;
rutes;
poblacions;
experiències.
sense que l'usuari hagi de fer consultes independents.

RF-05. Recomanacions
L'agent haurà de generar recomanacions adaptades a la informació proporcionada durant la conversa.
Les recomanacions podran tenir en compte:
ubicació;
dates;
tipus de viatge;
interessos;
perfil dels visitants;
altres condicionants expressats per l'usuari.

RF-06. Gestió del context
L'agent haurà de mantenir el context durant tota la conversa.
Les preguntes successives podran reutilitzar informació proporcionada anteriorment sense necessitat que l'usuari la torni a indicar.

RF-07. Gestió d'ambigüitats
Quan una pregunta sigui insuficient per generar una resposta fiable, l'agent haurà de demanar els aclariments mínims necessaris.
Per exemple:
"Què puc fer aquest cap de setmana?"
L'agent podrà preguntar:
"En quina comarca o població?"
Només quan aquesta informació sigui imprescindible.

RF-08. Gestió de resultats insuficients
Quan no existeixin coincidències exactes, l'agent haurà d'intentar ajudar l'usuari mitjançant estratègies alternatives.
Aquestes estratègies podran incloure:
ampliar la zona geogràfica;
suggerir activitats similars;
ampliar l'interval de dates;
proposar categories relacionades;
explicar la manca de resultats.

RF-09. Transparència
L'agent haurà d'indicar clarament quan:
no disposa d'informació;
la informació és parcial;
la resposta correspon a una recomanació.
En cap cas inventarà dades inexistents.

RF-10. Idiomes
L'agent haurà de respondre preferentment en l'idioma utilitzat per l'usuari.
La primera versió haurà de donar suport, com a mínim, a:
català;
castellà;
anglès.
francès.

RF-11. Navegació cap al portal
Sempre que sigui possible, les respostes inclouran referències als continguts corresponents de femturisme.cat.
L'objectiu és facilitar que l'usuari pugui ampliar la informació directament des del portal.

RF-12. Escalabilitat funcional
El sistema haurà de permetre incorporar noves fonts d'informació, nous tipus de contingut i noves funcionalitats sense modificar el comportament general de l'agent.
RF-13. Gestió documental per entitat
El sistema haurà de permetre gestionar documents associats a una entitat.
Aquesta gestió haurà d'incloure:
crear entitats;
modificar-les;
eliminar-les;
pujar documents;
consultar el llistat de documents;
veure l'estat d'indexació;
eliminar documents;
reindexar-los.
Cada entitat disposarà d'una base de coneixement pròpia i independent.
RF-14 Context operatiu
El mateix motor de l'agent haurà de poder funcionar en diferents contextos operatius.
Inicialment es contemplen dos modes:
Mode femturisme, amb accés a les fonts autoritzades del portal.
Mode entitat, amb accés exclusivament a la informació associada a l'entitat indicada.

RF-15 Integració amb entitats
Els elements del portal podran tenir associada una entity_id.
Quan el motor de l'agent treballi en mode femturisme i detecti aquesta associació, podrà consultar també la base de coneixement corresponent, sempre que aquesta funcionalitat estigui habilitada.


10. Requeriments no funcionals
Rendiment
L'agent haurà de proporcionar respostes en un temps compatible amb una conversa interactiva.

Disponibilitat
El sistema haurà d'estar disponible durant els períodes habituals de funcionament del portal.

Seguretat
L'agent només podrà accedir a les fonts d'informació autoritzades.

Escalabilitat
L'arquitectura haurà de permetre ampliar les funcionalitats de l'agent sense redissenyar completament el sistema.

Mantenibilitat
Les diferents fonts d'informació hauran de poder evolucionar de manera independent.

Traçabilitat
Les consultes realitzades per l'agent hauran de poder ser registrades amb finalitats de diagnòstic i millora contínua.
11. Restriccions del projecte
Fase 1
L'assistent treballarà exclusivament en mode femturisme.
La gestió d'entitats i les bases documentals independents formen part de la Fase 2.
Restriccions funcionals
La primera versió de l'agent treballarà exclusivament amb les fonts d'informació definides per femturisme.cat.
No formarà part de l'abast inicial:
consultar Internet de forma lliure;
executar consultes SQL generades pel model d'IA;
modificar informació del portal;
crear nous continguts;
interactuar amb sistemes de tercers.

Restriccions tècniques
L'accés a les dades es realitzarà únicament mitjançant mecanismes controlats pel sistema.
L'agent no tindrà accés directe ni il·limitat als sistemes d'informació del portal.

Restriccions de negoci
Les recomanacions de l'agent es basaran exclusivament en la informació disponible a les fonts autoritzades.
Quan aquesta informació sigui insuficient, l'agent haurà d'informar-ne l'usuari i intentar oferir alternatives dins del mateix ecosistema de femturisme.

12. Criteris d'acceptació
Es considerarà que la primera versió de l'agent compleix els objectius definits quan:
CA-01
L'usuari pugui interactuar amb l'agent mitjançant llenguatge natural.

CA-02
L'agent sigui capaç d'interpretar correctament la intenció de l'usuari en la majoria de consultes habituals.

CA-03
L'agent consulti les fonts d'informació necessàries sense que l'usuari conegui el seu funcionament intern.

CA-04
L'agent combini correctament informació procedent de diverses fonts quan la situació ho requereixi.

CA-05
Les respostes incloguin enllaços cap als continguts rellevants de femturisme.cat.

CA-06
Quan no existeixin coincidències exactes, l'agent proposi alternatives útils.

CA-07
L'agent mantingui el context durant tota la conversa.

CA-08
L'agent no inventi informació.

CA-09
El sistema permeti incorporar noves fonts d'informació sense modificar el model funcional de l'agent.

13. Indicadors d'èxit (KPIs)
Indicadors funcionals
Es definiran els següents indicadors per avaluar el comportament de l'agent una vegada desplegat en producció.
Indicador
Objectiu
Percentatge de consultes resoltes sense aclariments
> 70 %
Percentatge de consultes resoltes sense errors
> 95 %
Percentatge de consultes que retornen contingut rellevant
> 90 %
Temps mitjà de resposta
< 5 segons (objectiu inicial)
Percentatge de respostes amb enllaços a femturisme
Monitorització
Percentatge de consultes sense resposta
Monitorització
Percentatge de recomanacions acceptades pels usuaris
Evolució futura

(Les xifres són una proposta inicial; les podrem ajustar quan fem les proves pilot.)

14. Evolució prevista
El sistema es dissenyarà de manera modular per facilitar l'ampliació de funcionalitats en futures versions.
Entre les possibles línies d'evolució es consideren:
plataforma multi-entitat basada en un únic motor d'agent;
nous contextos operatius;
noves Tools;
integració de noves bases de coneixement.
incorporació de noves fonts internes d'informació;
integració amb fonts externes verificades;
ampliació a nous canals (WhatsApp, aplicació mòbil, etc.);
personalització de les recomanacions segons el perfil de l'usuari;
planificació automàtica d'itineraris;
integració amb sistemes de reserva;
suport a nous idiomes.

