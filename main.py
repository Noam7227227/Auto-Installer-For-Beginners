from langgraph.types import Command
from langchain_core.messages import HumanMessage
from src.utils import ui_log
from src.graph import print_event, build_graph


def main():
    app = build_graph()

    ui_log("Hi! Tell me what you want to set up or what you're trying to do.")
    user_input = input("You: ")

    config = {"configurable": {"thread_id": "session-1"}}

    initial_state = {
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
        "installation_guides": {},
        "installation_messages": [],
        "messages": [HumanMessage(content=user_input)],
    }

    ui_log("=== Starting installation run ===\n")

    for event in app.stream(initial_state, {**config, "recursion_limit": 50}):
        pass

    while True:
        graph_state = app.get_state(config)
        if not graph_state.next:
            break
        user_reply = input("You: ")
        app.invoke(Command(resume=user_reply), config)

    ui_log("\n=== Installation run complete ===")


if __name__ == "__main__":
    main()
