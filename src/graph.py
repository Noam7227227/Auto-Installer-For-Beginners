from langgraph.graph import StateGraph, END

from src.nodes import installments_filler
from src.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("installments_filler", installments_filler)

workflow.set_entry_point("installments_filler")
workflow.add_edge("installments_filler", END)

app = workflow.compile()
input = {"task": "I want to set up a Python development environment on my new laptop."}
result = app.invoke(input)

print(result["to_install"])