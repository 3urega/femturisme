"""
Tool registry — add new tools here.

Each tool module exposes:
  SCHEMA  : dict  — JSON schema in Anthropic format (name, description, input_schema)
  execute : callable(input: dict) -> str (JSON string)
"""
from .experiences     import SCHEMA as EXP_SCHEMA,     execute as exp_execute
from .accommodations  import SCHEMA as ACC_SCHEMA,     execute as acc_execute
from .events          import SCHEMA as EVT_SCHEMA,     execute as evt_execute
from .routes_tool     import SCHEMA as RTE_SCHEMA,     execute as rte_execute
from .local_knowledge import SCHEMA as LOC_SCHEMA,     execute as loc_execute

# Ordered list used by the agent
ALL_TOOLS: list[dict] = [
    EXP_SCHEMA,
    ACC_SCHEMA,
    EVT_SCHEMA,
    RTE_SCHEMA,
    LOC_SCHEMA,
]

_EXECUTORS: dict[str, callable] = {
    EXP_SCHEMA['name']: exp_execute,
    ACC_SCHEMA['name']: acc_execute,
    EVT_SCHEMA['name']: evt_execute,
    RTE_SCHEMA['name']: rte_execute,
    LOC_SCHEMA['name']: loc_execute,
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = _EXECUTORS.get(name)
    if fn is None:
        import json
        return json.dumps({'error': f'Unknown tool: {name}'})
    return fn(tool_input)
