from dataclasses import dataclass, field
from typing import Any


##################################################
# ACTION
##################################################

@dataclass
class Action:

    tool: str

    parameters: dict[str, Any] = field(
        default_factory=dict
    )


##################################################
# AI RESPONSE
##################################################

@dataclass
class AIResponse:

    actions: list[Action] = field(
        default_factory=list
    )

    ##################################################
    # LOCAL RESPONSE
    ##################################################

    text: str | None = None

    ##################################################
    # ROUTING INFO
    ##################################################

    local: bool = False