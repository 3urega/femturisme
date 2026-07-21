## Objetivo

Quan `search_establishments` (o qualsevol buscador de catàleg) retorna **3 o més** resultats rellevants, l'agent ha de **presentar almenys 3 opcions** amb enllaç a femturisme.cat, no resumir només 1.

## Contexto

Conversa reportada: després de «si» (acceptar cerca 30 km), l'agent va mostrar **només 1 hotel** (Hotel Estel) encara que el catàleg pot retornar més fitxes (`LIMIT 20` al repository).

No hi ha regla explícita al prompt avui; el LLM tendeix a respostes curtes. CA-05/CA-06 demanen recomanacions útils i alternatives.

## Alcance

| In | Fuera |
|----|-------|
| Regla de presentació al system prompt (`Com treballar` o `Resultats del catàleg`) | Canvis SQL o límit del repository |
| Exemple: si `total>=3` → llistar mínim 3 amb nom, ubicació, enllaç | Forçar 3 resultats quan `total<3` (honestedat CA-08) |
| Tests unitaris de presència de la regla | UAT script (issue #49) |

## Criterios de aceptación

- [ ] Prompt: si `total >= 3`, presentar **almenys 3** elements de `results[]` amb enllaços reals (CA-08).
- [ ] Si `total` és 1 o 2, llistar tots els disponibles sense inventar.
- [ ] `pytest tests/unit/test_prompts.py -q` passa.

## Capas / archivos principales

- [`app/prompts/femturisme.py`](../../app/prompts/femturisme.py)
- [`tests/unit/test_prompts.py`](../../tests/unit/test_prompts.py)

## Issues relacionadas

- #46 — més resultats possibles amb radi
- #49 — UAT valida presentació

## Referencias

- [requeriments.md CA-05, CA-06](../../client/requeriments.md)
- [plan-establishments-proximity.md](../devs/plan-establishments-proximity.md)

## Verificación

```bash
pytest tests/unit/test_prompts.py -q
```
