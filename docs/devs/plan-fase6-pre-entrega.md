# Pla: Fase 6 — Pre-entrega (sense PHP)

Tancar qualitat i verificació de l'agent al **xat Flask** abans de reprendre Fase 4 (widget PHP).

**Estat:** batch publicat a GitHub *(2026-07-14)*.

**Prerequisits tancats:** DEV-600, DEV-601, DEV-603, DEV-604 (Fase 6 parcial).

---

## Ordre d'implementació

1. **Rate limiting + logging** (DEV-602) — observabilitat i protecció API
2. **UAT context CA-07** — memòria de sessió multi-turn
3. **Matriu CA-01…CA-09** (DEV-605) — evidència Fase 1
4. **sql-mapeo.md** (DEV-010) — SQL provada, sense TBD crítics

La Fase 4 (#18–#22) roman en espera fins accés PHP/staging.

---

## GitHub issues (draft → publicat)

| Slug | Títol | Labels | Depèn de |
|------|-------|--------|----------|
| `rate-limiting-logging.md` | Fase 6: Rate limiting i logging minim (DEV-602) | fase-6, agent, ops | — | [#23](https://github.com/3urega/femturisme/issues/23) **tancat** |
| `uat-conversation-context.md` | Fase 6: UAT context conversacional CA-07 | fase-6, agent, testing | — | [#24](https://github.com/3urega/femturisme/issues/24) |
| `ca-matrix-verification.md` | Fase 6: Matriu CA-01 a CA-09 (DEV-605) | fase-6, testing, docs | #24 | [#25](https://github.com/3urega/femturisme/issues/25) |
| `sql-mapeo-completion.md` | Fase 6: Tancar sql-mapeo.md 6 buscadors (DEV-010) | fase-6, mysql, docs | — | [#26](https://github.com/3urega/femturisme/issues/26) |

Manifest: [manifest.fase6-pre-entrega.json](../issues/manifest.fase6-pre-entrega.json)

---

## Fora d'abast d'aquest batch

- Widget globus, proxy nginx, UAT responsive (Fase 4)
- RAG / PostgreSQL admin (Fase 5)
- Sign-off client staging (DEV-606)
- Truncat 6 cards (DEV-309 → Fase 9)

---

## Referències

- [checklist-entrega.md](checklist-entrega.md) — DEV-602, DEV-605, DEV-010
- [plan-fase4-php-widget.md](plan-fase4-php-widget.md) — Fase 4 posposada
