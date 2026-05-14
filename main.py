from src.graph import print_event, build_graph


def main():
    app = build_graph()

    initial_state = {
        "task" : "dowanload canvas, python 3.12, and git",
        "to_install": [],
        "installation_guides": {},
        "messages": [],
    }

    print("=== Starting installation run ===\n")
    for event in app.stream(initial_state, {"recursion_limit": 50}):
        print_event(event)
    print("\n=== Installation run complete ===")


if __name__ == "__main__":
    main()
