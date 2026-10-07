from backend.planner import Planner
from automation.executors.engine import AutomationEngine


planner = Planner()

engine = AutomationEngine()


print("\n========== JARVIS TEST ==========\n")

while True:

    command = input(">>> ")

    if command.lower() in ("exit", "quit"):

        break

    actions = planner.plan(command)

    print("\nActions:")

    for action in actions:

        print(action)

    print()

    engine.execute(actions)