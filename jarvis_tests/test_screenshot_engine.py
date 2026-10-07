from backend.planner import Planner
from automation.executors.engine import AutomationEngine


planner = Planner()

engine = AutomationEngine()

commands = [

    "take screenshot",

    "save screenshot as desktop.png"

]

for command in commands:

    print(f"\n>>> {command}")

    actions = planner.plan(command)

    engine.execute(actions)