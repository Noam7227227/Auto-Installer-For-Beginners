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
    install_filler,
    research_installer,
    software_installer_node,
    lc_tools
)
from langgraph.prebuilt import ToolNode, tools_condition
from src.state import AgentState

def route_after_interpreter(state: AgentState) -> str:
    return "suggest_main_apps" if state.get("interpreter_ready") else "human_input"

def route_after_picking_main(state: AgentState) -> str:
    return "finalize_consumption" if state.get("task_type") == "consumption" else "suggest_side_tools"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("interpreter",               interpreter)
    workflow.add_node("human_input",               human_input)
    workflow.add_node("suggest_main_apps",         suggest_main_apps)
    workflow.add_node("human_picks_main",          human_picks_main)
    workflow.add_node("finalize_consumption",      finalize_consumption)
    workflow.add_node("suggest_side_tools",        suggest_side_tools)
    workflow.add_node("human_confirms_side_tools", human_confirms_side_tools)

    workflow.set_entry_point("interpreter")
    workflow.add_node("download_researcher", research_installer)
    workflow.add_node("installer", software_installer_node)
    workflow.add_node("tools", ToolNode(lc_tools))
    
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
    workflow.add_edge("finalize_consumption",      "download_researcher")
    workflow.add_edge("suggest_side_tools",        "human_confirms_side_tools")
    workflow.add_edge("human_confirms_side_tools", "download_researcher")
    workflow.add_edge("download_researcher", "installer")
    workflow.add_conditional_edges("installer", tools_condition)
    workflow.add_edge("tools", "installer")
    return workflow.compile(checkpointer=MemorySaver())

def print_event(event: dict):
    """Prints only AI messages, tool calls, and tool results."""
    for node_update in event.values():
        # Ensure we're looking at a dictionary with a messages key
        if not isinstance(node_update, dict):
            continue
            
        msgs = node_update.get("messages", [])
        for msg in msgs:
            mtype = type(msg).__name__

            if mtype == "AIMessage":
                # 1. Print the intent to call a tool
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        print(f"🛠️  [Tool Call] {tc['name']}({tc['args']})")
                
                # 2. Print what the AI is actually saying to the user
                if msg.content:
                    print(f"🤖 [AI] {msg.content}")

            elif mtype == "ToolMessage":
                # 3. Print the result coming back from your system commands
                print(f"💾 [Tool Result] {msg.content}")