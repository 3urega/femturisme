## Objetivo

Documentar la integració **same-origin**: reverse proxy `/api/chat` i `/api/session/reset` des de femturisme.cat cap al servei Python, amb headers SSE correctes.

## Contexto

- ADR-008: navegador només parla amb femturisme.cat; PHP/proxy reenvia a Python.
- Snippets nginx a [tecnic.md](../client/tecnic.md) §4.8; cal guia operativa per devs/ops i checklist aplicable.
- Headers `X-Accel-Buffering: no`, `proxy_buffering off`, timeouts — DEV-406.
- El codi del proxy viu al servidor/CMS client; aquest repo aporta **documentació i exemples**.

## Alcance

| In | Fuera |
|----|-------|
| `docs/devs/php-proxy-integration.md` (nginx + apache + notes PHP) | Desplegament real al servidor client |
| Exemples `location /api/chat` i `/api/session/reset` | Autenticació interna P-01 (esbossar opcions) |
| Checklist verificació same-origin (sense CORS al navegador) | VPN / xarxa DEV-027 |
| Referència a variables `HOST_AGENT`, `PORT` | Widget JS |

## Criterios de aceptación

- [ ] Doc amb snippets nginx i apache copiables
- [ ] Headers SSE documentats (`X-Accel-Buffering: no`, buffering off, timeouts recomanats)
- [ ] Procediment smoke: `curl` same-origin o via proxy staging → SSE `done`
- [ ] Enllaç des de `desenvolupament-local.md` o `testing.md`
- [ ] Sense secrets al repo

## Capas / archivos principales

- `docs/devs/php-proxy-integration.md` (nou)
- `docs/devs/desenvolupament-local.md` (enllaç)
- Opcional: `docs/client/tecnic.md` — enllaç a guia dev

## Issues relacionadas

- `widget-globus-assets.md`
- `uat-widget-staging.md`

## Verificación

```powershell
# Doc review + smoke quan staging disponible:
curl -s http://127.0.0.1:5010/health
curl -N -X POST http://127.0.0.1:5010/api/chat -H "Content-Type: application/json" -d "{\"message\":\"hola\",\"session_id\":\"test\"}"
```

## Referencias

- [tecnic.md](../client/tecnic.md) §4.8, §11.2
- [checklist-entrega.md](../devs/checklist-entrega.md) DEV-401, DEV-406
