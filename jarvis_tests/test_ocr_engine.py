from backend.planner import Planner
from automation.executors.engine import AutomationEngine


planner = Planner()

engine = AutomationEngine()

commands = [

    "ocr screen"

]

for command in commands:

    print(f"\n>>> {command}")

    actions = planner.plan(command)

    engine.execute(actions)