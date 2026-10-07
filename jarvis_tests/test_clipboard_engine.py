from backend.planner import Planner
from automation.executors.engine import AutomationEngine
from automation.clipboard.service import ClipboardService


planner = Planner()

engine = AutomationEngine()

clipboard = ClipboardService()

commands = [

    "copy Hello from JARVIS X",

    "read clipboard",

    "clear clipboard",

    "read clipboard"

]

for command in commands:

    print(f"\n>>> {command}")

    actions = planner.plan(command)

    engine.execute(actions)

print("\nFinal Clipboard:")

print(

    repr(

        clipboard.read()

    )

)