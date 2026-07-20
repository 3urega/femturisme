## Objetivo

Actualitzar el **system prompt** perquè el LLM faci routing correcte en consultes **temàtiques o informatives** (qualsevol terme cercable: festa, patrimoni, activitat, lloc…) i no confongui «informació sobre X» amb absència de tool.

**Patum és un exemple il·lustratiu** al prompt — les regles han de ser genèriques («X», «tema», «activitat»), no una llista tancada de festivals.

## Contexto

- [funcional.md §6](../client/funcional.md) distingeix preguntes d'**informació** i **agenda**; aplica a qualsevol tema, no només Patum.
- [`femturisme.py`](../../app/prompts/femturisme.py) té guies per domini però no una secció explícita per **consultes sense territori clar**.
- Complementa heurístiques server-side ([#37](https://github.com/3urega/femturisme/issues/37)); millora routing quan el LLM tria sol.

## Alcance

| In | Fuera |
|----|-------|
| Secció prompt «Consultes temàtiques / informatives» amb regles genèriques | Reescriure tot el prompt |
| ≥3 exemples diversos (p.ex. Patum, castellers, mercat medieval) — cadascun amb tools esperades | Llista exhaustiva de festivals al prompt |
| Regla: no respondre «no sé» sense haver provat `search_articles(query/topic)` i `search_events(query)` quan hi ha terme cercable | Canvis a SCHEMA tools (issue #36) |
| Distinció: explicació → articles; data/calendari → events amb query | Whitelist hardcoded al codi |

## Criterios de aceptación

- [ ] Prompt inclou regla genèrica + ≥3 exemples **diferents** (inclou Patum com a un d'ells, no l'únic)
- [ ] Distinció clara: explicació → articles; data → events amb query
- [ ] `pytest tests/unit/test_prompts.py` actualitzat si existeix snapshot
- [ ] Revisió manual dummy LLM: millora routing en consultes Patum **i** almenys 2 temes no relacionats (p.ex. castellers, ruta del vi)

## Capas / archivos principales

- `app/prompts/femturisme.py`
- `tests/unit/test_prompts.py` (si aplica)

## Issues relacionadas

- [#37](https://github.com/3urega/femturisme/issues/37) agent-theme-routing
- [#40](https://github.com/3urega/femturisme/issues/40) uat-catalog-recall-battery

## Verificación

```powershell
python -m pytest tests/unit/test_prompts.py -v
```

## Referencias

- [plan-catalog-recall.md](../devs/plan-catalog-recall.md)
- [requeriments.md](../client/requeriments.md) RF-02, RF-03
