from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.services.agent_service import AgentService

QUESTION = (
    "Recomana'm una ruta de senderisme fàcil per fer en família a Catalunya"
)

app = create_app()
with app.app_context():
    agent = AgentService(provider=app.config["LLM_PROVIDER"])
    for ev in agent.run(QUESTION, "test-routes-family"):
        t = ev.get("type")
        if t == "tool_call":
            print("TOOL_CALL", ev.get("tool"), ev.get("input"))
        elif t == "tool_result":
            r = ev.get("result", {})
            print(
                "TOOL_RESULT",
                ev.get("tool"),
                "total=",
                r.get("total") if isinstance(r, dict) else None,
                "error=",
                r.get("error") if isinstance(r, dict) else None,
            )
        elif t == "error":
            print("ERROR", ev.get("message"))
        elif t == "done":
            print("DONE")
            print("---TEXT---")
            print(ev.get("full_text", "")[:1500])
