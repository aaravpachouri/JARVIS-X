from ai.tools import TOOLS


class AIValidator:

    ##################################################

    def validate(self, response):

        valid_actions = []

        for action in response.actions:

            if action.tool not in TOOLS:

                print(f"[Validator] Unknown tool: {action.tool}")

                continue

            valid_actions.append(action)

        response.actions = valid_actions

        return response