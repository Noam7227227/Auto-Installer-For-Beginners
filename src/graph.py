from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from src.nodes import install_filler, research_installer, software_installer_node, lc_tools
from src.state import AgentState


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("installer_filler", install_filler)
    workflow.add_node("download_researcher", research_installer)
    workflow.add_node("installer", software_installer_node)
    workflow.add_node("tools", ToolNode(lc_tools))
    
    workflow.set_entry_point("installer_filler")
    workflow.add_edge("installer_filler", "download_researcher")
    workflow.add_edge("download_researcher", "installer")
    workflow.add_conditional_edges("installer", tools_condition)
    workflow.add_edge("tools", "installer")
    return workflow.compile()


def print_event(event: dict):
    """Pretty-print streaming updates from the graph, including state changes."""
    for node_name, node_update in event.items():
        print(f"\n--- Node: {node_name} ---")
        
        # 1. Print state updates (excluding messages for now)
        if isinstance(node_update, dict):
            for key, value in node_update.items():
                if key != "messages":
                    print(f"[State Update] {key}: {value}")

        # 2. Print messages (AI thoughts and Tool outputs)
        msgs = node_update.get("messages", []) if isinstance(node_update, dict) else []
        for msg in msgs:
            mtype = type(msg).__name__

            if mtype == "AIMessage":
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        print(f"[AI -> tool] {tc['name']}({tc['args']})")
                if msg.content:
                    print(f"[AI says] {msg.content}")

            elif mtype == "ToolMessage":
                print(f"[Tool '{msg.name}' returned] {msg.content}")

