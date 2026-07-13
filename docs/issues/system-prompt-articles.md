## Objetivo

Actualitzar el system prompt per reflectir **`search_articles`** disponible al registry (DEV-310 ampliació). Eliminar l'estat «pendent» del 6è domini.

## Contexto

- #10 va crear `app/prompts/femturisme.py` amb articles marcat com *pendent* (tool no existia).
- Després de `articles-repository-mysql`, el prompt ha de instruir el LLM a usar `search_articles` per notícies/editorial.
- Llista dinàmica `ALL_TOOLS` ja es genera en runtime; cal actualitzar secció dominis i regles.

## Alcance

| In | Fuera |
|----|-------|
| `app/prompts/femturisme.py` — domini articles actiu | Reescriure tot el prompt |
| Tabla dominis: articles = disponible | Mode entitat |
| `tests/unit/test_prompts.py` ampliat si cal | Canvis a tool schemas |

## Criterios de aceptación

- [ ] Prompt no diu que `search_articles` és pendent
- [ ] Prompt distingeix articles (notícies/editorial) vs agenda vs experiències
- [ ] `search_articles` apareix a guia de routing
- [ ] `tests/unit/test_prompts.py` passa
- [ ] `python -m pytest -v` passa

## Capas / archivos principales

- `app/prompts/femturisme.py`
- `tests/unit/test_prompts.py`

## Verificación

```powershell
python -m pytest tests/unit/test_prompts.py -v
python -m pytest -v
```

## Issues relacionadas

- [#12](https://github.com/3urega/femturisme/issues/12) ArticlesRepository
- [#15](https://github.com/3urega/femturisme/issues/15) Registry 6 MySQL

## Referencias

- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-310
- Issue #10 (system prompt base)
