from langgraph.types import Command
from langchain_core.messages import HumanMessage
from src.graph import app

config = {"configurable": {"thread_id": "session-1"}}

print("Hi! Tell me what you want to set up or what you're trying to do.")
user_input = input("You: ")

app.invoke(
    {
        "task": "",
        "to_install": [],
        "interpreter_ready": False,
        "task_type": None,
        "task_medium": None,
        "paid_preference": None,
        "main_app_options": [],
        "chosen_main_app": "",
        "side_tools": [],
        "web_options": [],
        "messages": [HumanMessage(content=user_input)],
    },
    config,
)

while True:
    graph_state = app.get_state(config)
    if not graph_state.next:
        break
    user_reply = input("You: ")
    app.invoke(Command(resume=user_reply), config)

final = app.get_state(config).values
print("\n── Final installation list ──────────────────")
for item in final.get("to_install", []):
    print(f"  • {item}")
if not final.get("to_install"):
    print("  (no installation needed — web-based solution)")