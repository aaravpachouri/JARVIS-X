import time

from automation.services.app_service import AppService
from backend.planner import Planner
from automation.executors.engine import AutomationEngine


def main():

    apps = AppService()

    planner = Planner()

    engine = AutomationEngine()

    print("Opening Notepad...")

    if not apps.open("notepad"):

        print("Could not open Notepad.")

        return

    time.sleep(2)

    commands = [

        "maximize notepad",

        "restore notepad",

        "minimize notepad",

        "restore notepad",

        "focus notepad"

    ]

    for command in commands:

        print(f">>> {command}")

        actions = planner.plan(command)

        engine.execute(actions)

        time.sleep(2)


if __name__ == "__main__":

    main()