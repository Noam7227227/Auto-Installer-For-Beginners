from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.nodes import (
    interpreter,
    human_input,
    suggest_main_apps,
    human_picks_main,
    finalize_consumption,
    suggest_side_tools,
    human_confirms_side_tools,
)
from src.state import AgentState

def route_after_interpreter(state: AgentState) -> str:
    return "suggest_main_apps" if state.get("interpreter_ready") else "human_input"

def route_after_picking_main(state: AgentState) -> str:
    return "finalize_consumption" if state.get("task_type") == "consumption" else "suggest_side_tools"

workflow = StateGraph(AgentState)

workflow.add_node("interpreter",               interpreter)
workflow.add_node("human_input",               human_input)
workflow.add_node("suggest_main_apps",         suggest_main_apps)
workflow.add_node("human_picks_main",          human_picks_main)
workflow.add_node("finalize_consumption",      finalize_consumption)
workflow.add_node("suggest_side_tools",        suggest_side_tools)
workflow.add_node("human_confirms_side_tools", human_confirms_side_tools)

workflow.set_entry_point("interpreter")

workflow.add_conditional_edges("interpreter", route_after_interpreter, {
    "suggest_main_apps": "suggest_main_apps",
    "human_input":       "human_input",
})
workflow.add_conditional_edges("human_picks_main", route_after_picking_main, {
    "finalize_consumption": "finalize_consumption",
    "suggest_side_tools":   "suggest_side_tools",
})

workflow.add_edge("human_input",               "interpreter")
workflow.add_edge("suggest_main_apps",         "human_picks_main")
workflow.add_edge("finalize_consumption",      END)
workflow.add_edge("suggest_side_tools",        "human_confirms_side_tools")
workflow.add_edge("human_confirms_side_tools", END)

app = workflow.compile(checkpointer=MemorySaver())