from src.graph import _print_event, build_graph


def main():
    app = build_graph()

    initial_state = {
        "task" : "Set up a Python development environment with Git and Python 3.12.",
        "to_install": [],
        "messages": [],
    }

    print("=== Starting installation run ===\n")
    for event in app.stream(initial_state, {"recursion_limit": 50}):
        _print_event(event)
    print("\n=== Installation run complete ===")


if __name__ == "__main__":
    main()
