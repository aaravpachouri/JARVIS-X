import subprocess

from core.actions import ActionType


class TerminalExecutor:

    def __init__(self):

        pass

    ##################################################

    def execute(self, action):

        match action.action:

            ##################################################

            case ActionType.RUN_COMMAND:

                self.runCommand(

                    action.parameters["command"]

                )

            ##################################################

            case ActionType.RUN_PYTHON:

                self.runPython(

                    action.parameters["script"]

                )

            ##################################################

            case _:

                print(

                    f"[Terminal] Unsupported action: {action.action.name}"

                )

    ##################################################

    def runCommand(self, command):

        try:

            result = subprocess.run(

                command,

                shell=True,

                capture_output=True,

                text=True

            )

            print()

            print("=" * 60)

            print("COMMAND OUTPUT")

            print("=" * 60)

            print(result.stdout)

            if result.stderr:

                print(result.stderr)

            print("=" * 60)

            print()

            return result

        except Exception as e:

            print(e)

    ##################################################

    def runPython(self, script):

        self.runCommand(

            f'python "{script}"'

        )