Estrategia que encaja con vuestro repo
1. Separar por determinismo antes de refactorizar
No refactorizar «el agente» como bloque. Extraer módulos pequeños con contrato claro:

AgentService (orquestación fina)
  ├── domain_hints.py      ← inferir domini actiu (test unitario)
  ├── query_keywords.py    ← fallback temàtic (ya testeado)
  ├── period_hints.py      ← agenda (patrón a copiar)
  └── prompts/femturisme.py ← reglas de negocio LLM (test_prompts.py)
Cada extracción debe llevar tests unitarios que fallen si cambia la regla, no solo si cambia el comentario.

2. Tres niveles de red de seguridad (de barato a caro)
Nivel A — Unitarios (rápidos, CI siempre)
Lo que ya tenéis y funciona bien:

test_prompts.py: presencia de reglas críticas (domini, Berga, prohibit…)
test_query_keywords.py, test_catalog_fallback.py
Futuro test_domain_hints.py (#52)
Son baratos y detectan regresiones de reglas escritas, no de comportamiento LLM real.

Nivel B — API con LLM mock (tests/api/test_chat.py + mock_tool_execute)
Sirven para comprobar que el bucle sigue bien: SSE, orden tool_call → tool_result → done, inyección de hints, skip de fallback.
Ampliaría esto con escenarios multi-turn mockeando la respuesta del LLM (qué tool elige) para validar que server-side corrige o guía bien, sin depender del proveedor.

Nivel C — UAT conversacionales (gate pre-merge / pre-release)
Scripts que ya tenéis:

uat_catalog_battery.py — routing 12 dominios
uat_patum_bergua_accommodation.py — multi-turn Patum→Berga
uat_experiences_radius.py, uat_recall_battery.py, etc.
Estos son la única forma fiable de detectar regresiones end-to-end con LLM real. Un refactor de agente debería exigir: «batería X sigue ≥ umbral Y».

3. Tests de caracterización, no solo comentarios
Antes de tocar AgentService, congelar comportamiento actual con tests que documenten entrada → efecto observable:

# Ejemplo de intención, no código a implementar ya
def test_with_system_injects_agenda_hint_when_agenda_query():
    messages = service._with_system([], user_message="Què fem aquest cap de setmana?")
    assert "Instrucció d'aquest torn" in messages[0]["content"]
Eso es más útil que un comentario largo: el test falla si el refactor rompe el contrato.

4. Invariantes explícitas (mejor que comentarios sueltos)
En lugar de esparcir instrucciones por el código, un bloque corto en agente.md o un docs/devs/agent-invariants.md:

Agenda ≠ experiències
Proximitat km: domini conversacional determina eina
Seguiment allotjament: només establishments
Fase 1: sense RAG públic
Cada invariante enlazada a 1 test unitario + 1 caso UAT (si existe). El comentario en código solo dice: «veure invariant #3 + test_domain_hints».

5. Refactor vertical, no horizontal
El plan de #50–#52 es el patrón correcto:

Un slice = un CA verificable
Mergeable solo
No «primero reescribo AgentService entero»
Eso reduce el radio de explosión de una regresión.