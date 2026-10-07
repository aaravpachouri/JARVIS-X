from backend.planner import Planner
from automation.executors import AutomationEngine


planner = Planner()
engine = AutomationEngine()

print("=" * 60)
print("          JARVIS AUTOMATION TEST CONSOLE")
print("=" * 60)

while True:

    command = input("\nJarvis > ").strip()

    if command.lower() in ["exit", "quit"]:
        print("\nGoodbye.\n")
        break

    if not command:
        continue

    actions = planner.plan(command)

    print("\nActions:")

    for action in actions:

        print(
            f"• {action.action.name} -> {action.parameters}"
        )

    print()

    engine.execute(actions)