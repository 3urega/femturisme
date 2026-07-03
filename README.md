# agent_femturisme

Assistent de xat per a [femturisme.cat](https://www.femturisme.cat) — Flask + LLM + buscadors MySQL.

**Agents / documentació:** [AGENTS.md](AGENTS.md) · [docs/devs/index.md](docs/devs/index.md)

---

## Arrancar en local (Windows, sense Docker)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
# Edita .env: provider LLM + API key del client (veure sota)
python main.py
```

Obre **http://127.0.0.1:5010** (widget de xat demo).

| Acció | Comanda |
|-------|---------|
| Tests | `python -m pytest -v` |
| Aturar | `Ctrl+C` |

**LLM en local:** posa la **API key del client** al `.env` i el provider que useu (`anthropic`, `openai` o `gemini`). El xat funcionarà com en producció. No cal Docker ni MySQL per arrencar.

```env
AGENT_LLM_PROVIDER=anthropic
AGENT_ANTHROPIC_API_KEY=sk-ant-...   # clau del client — no pujar al repo
```

El mode `dummy` només s'usa als **tests** automàtics (`pytest`), no cal per desenvolupar manualment.

---

## Més informació

| Document | Contingut |
|----------|-----------|
| **[docs/devs/desenvolupament-local.md](docs/devs/desenvolupament-local.md)** | Guia completa: venv, `.env`, ports, MySQL remot, troubleshooting |
| [docs/devs/testing.md](docs/devs/testing.md) | pytest, API-01…04 |
| [docs/client/tecnic.md](docs/client/tecnic.md) | API, desplegament staging/prod |

Docker (`docker-compose.yml`) és només per **staging/producció** al servidor del client.
