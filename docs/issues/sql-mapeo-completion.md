## Objetivo

Cerrar **DEV-010**: `sql-mapeo.md` completo para los 6 buscadors, sin secciones TBD críticas y con casos de prueba SQL validados contra el dump local.

## Contexto

- DEV-010 está **parcial**: schema mapeado y SQL borrador; falta validación con datos reales y cierre de preguntas abiertas (URLs canónicas, vigencia, idioma `fr`).
- Refuerza calidad de respuestas del agente sin tocar PHP.
- Relacionado con **DEV-024…DEV-026** (preguntas cliente); cerrar lo verificable con dump local.

## Alcance

| In | Fuera |
|----|-------|
| Revisar 6 secciones de `sql-mapeo.md` (establishments, articles, destinations, events, experiences, routes) | Cambios de esquema MySQL en CMS |
| Ejecutar SQL-01…SQL-07 contra dump local; actualizar asserts esperados | Staging remoto sin acceso |
| Documentar URLs canónicas femturisme.cat por tipo de ficha | Traducción masiva de contenido CMS |
| Sección idioma: `ca/es/en/fr` + nota contenido parcial | Nuevos buscadors (fuera v1) |
| Marcar TBD restantes con owner (cliente vs dev) | Implementación PHP |

## Criterios de aceptación

- [ ] Cada buscador tiene: tablas, SQL final, mapatge JSON, ≥1 caso prueba con resultado documentado (total ≥0 aceptable)
- [ ] SQL-01…SQL-07 pasan en `pytest tests/integration/sql/` contra MySQL local
- [ ] Sin TBD críticos en filtros de vigencia/publicación sin nota de decisión
- [ ] URLs canónicas documentadas o enlace a `tecnic.md` §6 con ejemplo por dominio
- [ ] Checklist **DEV-010** marcado; progreso checklist actualizado
- [ ] Preguntas no resolubles localmente listadas en `tecnic.md` §8.3 con estado

## Capas / archivos principales

- `docs/sql-mapeo.md`
- `tests/integration/sql/test_*.py`
- `docs/client/tecnic.md` §8.3 (preguntas obertes)
- `docs/devs/checklist-entrega.md` — DEV-010

## Issues relacionadas

- [#25](https://github.com/3urega/femturisme/issues/25) (DEV-605, tancada) — [ca-matrix-fase1.md](../devs/ca-matrix-fase1.md)

## Verificación

```powershell
python -m pytest tests/integration/sql/ -v
# Revisar docs/sql-mapeo.md: cap secció sense SQL ni cas prova
```

## Referencias

- [sql-mapeo.md](../sql-mapeo.md)
- [dominio-femturisme-ca.md](../client/dominio-femturisme-ca.md) §5, §7
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-010, DEV-024…026
