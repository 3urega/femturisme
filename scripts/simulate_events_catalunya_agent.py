"""Full agent simulation for events Catalunya this month."""
import _bootstrap  # noqa: F401

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.services.agent_service import AgentService

QUESTION = "Quins events i fires hi ha a Catalunya aquest mes?"

app = create_app()
with app.app_context():
    agent = AgentService(provider=app.config["LLM_PROVIDER"])
    for ev in agent.run(QUESTION, "sim-events-catalunya"):
        t = ev.get("type")
        if t == "tool_call":
            print("TOOL_CALL", ev.get("tool"), ev.get("input"))
        elif t == "tool_result":
            r = ev.get("result", {})
            print(
                "TOOL_RESULT",
                ev.get("tool"),
                "total=", r.get("total") if isinstance(r, dict) else None,
                "meta=", (r.get("meta") if isinstance(r, dict) else None),
            )
        elif t == "error":
            print("ERROR", ev.get("message"))
        elif t == "done":
            print("---RESPOSTA AGENT---")
            print(ev.get("full_text", ""))
