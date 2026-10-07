from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from core.actions import Action as CoreAction
from core.actions import ActionType
from automation.browser_intelligence import BrowserIntelligence
from automation.ui_element_targeting import UIElementTargeting
from automation.executors.filesystem_executor import FilesystemExecutor


class AgentToolset:

    """
    Universal bridge between the local AI brain and the
    existing AutomationEngine.

    IMPORTANT:

    This class does NOT contain application-specific logic.

    It exists to make the AI -> ActionType -> AutomationEngine
    contract reliable for ANY supported computer task.
    """

    ############################################################
    # INTERNAL AGENT-LEVEL OPERATIONS
    ############################################################

    INTERNAL = {
        "RECORD",
        "CREATE_SPREADSHEET",
        "APPEND_SPREADSHEET",
        "REMEMBER",
        "FINISH",
    }

    ############################################################
    # COMMON PARAMETER ALIASES
    #
    # These are UNIVERSAL aliases.
    #
    # Example:
    #
    # target:
    # text:
    # label:
    #
    # may all represent the same textual UI target for tools
    # that operate on visible text.
    ############################################################

    PARAMETER_ALIASES = {

        "target": (
            "target",
            "text",
            "label",
            "name",
            "value",
        ),

        "text": (
            "text",
            "value",
            "content",
            "string",
        ),

        "app": (
            "app",
            "app_name",
            "application",
            "application_name",
            "program",
            "program_name",
            "name",
        ),

        "url": (
            "url",
            "uri",
            "link",
            "address",
        ),

        "key": (
            "key",
            "button",
            "key_name",
        ),

        "seconds": (
            "seconds",
            "duration",
            "delay",
        ),

        "window": (
            "window",
            "window_title",
            "title",
            "target",
            "app",
            "app_name",
            "application",
            "application_name",
            "program",
            "program_name",
            "name",
        ),
    }

    ############################################################
    # ACTION TYPES
    #
    # Keep this capability-based.
    #
    # Nothing here is tied to a particular application.
    ############################################################

    _ACTION_NAMES = (
        "OPEN_APP",
        "CLOSE_APP",

        "OPEN_URL",
        "SEARCH_WEB",

        "CREATE_FILE",
        "CREATE_FOLDER",
        "COPY",
        "MOVE",
        "RENAME",

        "MOUSE_MOVE",
        "MOUSE_MOVE_CENTER",
        "LEFT_CLICK",
        "RIGHT_CLICK",
        "DOUBLE_CLICK",
        "SCROLL_UP",
        "SCROLL_DOWN",
        "DRAG",

        "TYPE_TEXT",
        "PRESS_KEY",
        "HOTKEY",
        "HOLD_KEY",
        "RELEASE_KEY",

        "FOCUS_WINDOW",
        "CLOSE_WINDOW",
        "MINIMIZE_WINDOW",
        "MAXIMIZE_WINDOW",
        "RESTORE_WINDOW",
        "MOVE_WINDOW",
        "RESIZE_WINDOW",

        "READ_CLIPBOARD",
        "WRITE_CLIPBOARD",
        "CLEAR_CLIPBOARD",

        "TAKE_SCREENSHOT",
        "TAKE_REGION_SCREENSHOT",
        "TAKE_WINDOW_SCREENSHOT",
        "SAVE_SCREENSHOT",

        "OCR_SCREEN",
        "OCR_IMAGE",

        "LOCATE_TEXT",
        "CLICK_TEXT",
        "CLICK_TYPE_ENTER",

        "RUN_COMMAND",
        "RUN_PYTHON",

        "VOLUME",
        "BRIGHTNESS",

        "WAIT",
        "NOTIFY",
    )

    ############################################################
    # CONSTRUCTION
    ############################################################

    def __init__(
        self,
        engine=None
    ):

        self.engine = engine

        ############################################################
        # BROWSER INTELLIGENCE
        #
        # Deterministic browser operations are handled here.
        # ComputerUseAgent remains responsible for visual and
        # semantic verification of the resulting computer state.
        ############################################################

        self.browser = (
            BrowserIntelligence()
        )

        ############################################################
        # UI ELEMENT TARGETING
        #
        # Semantic resolver for CLICK_TEXT / LOCATE_TEXT style
        # operations. It identifies targets but never performs the
        # interaction itself.
        ############################################################

        self.ui_targeting = (
            UIElementTargeting()
        )

        ############################################################
        # FILESYSTEM EXECUTOR
        #
        # Deterministic mutation layer. FileIntelligence remains
        # responsible for discovery/ranking in ComputerUseAgent.
        ############################################################

        self.filesystem = (
            FilesystemExecutor()
        )

        self.ACTION_MAP = (
            self._build_action_map()
        )

    ############################################################
    # BUILD ACTION MAP
    ############################################################

    @staticmethod
    def _build_action_map():

        mapping = {}

        for name in AgentToolset._ACTION_NAMES:

            action_type = getattr(
                ActionType,
                name,
                None
            )

            if action_type is not None:

                mapping[
                    name
                ] = action_type

        return mapping

    ############################################################
    # AVAILABLE
    ############################################################

    def available(
        self
    ):

        tools = list(
            self.ACTION_MAP.keys()
        )

        tools.extend(
            sorted(
                self.INTERNAL
            )
        )

        return tools

    ############################################################
    # HAS TOOL
    ############################################################

    def has(
        self,
        tool
    ):

        name = (
            self.normalize_tool(
                tool
            )
        )

        return (
            name in self.ACTION_MAP
            or
            name in self.INTERNAL
        )

    ############################################################
    # NORMALIZE TOOL NAME
    ############################################################

    @staticmethod
    def normalize_tool(
        tool
    ):

        return str(
            tool or ""
        ).strip().upper()

    ############################################################
    # NORMALIZE PARAMETERS
    ############################################################

    def normalize_parameters(
        self,
        tool,
        parameters
    ):

        tool = (
            self.normalize_tool(
                tool
            )
        )

        if not isinstance(
            parameters,
            dict
        ):

            parameters = {}

        source = dict(
            parameters
        )

        normalized = dict(
            source
        )

        ########################################################
        # UNIVERSAL ALIASES
        ########################################################

        if tool in {
            "CLICK_TEXT",
            "LOCATE_TEXT",
            "CLICK_TYPE_ENTER",
        }:

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "target"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "target"
                ] = value

        ########################################################
        # TEXT-BASED ACTIONS
        ########################################################

        if tool in {
            "TYPE_TEXT",
            "WRITE_CLIPBOARD",
            "NOTIFY",
        }:

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "text"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "text"
                ] = value

        ########################################################
        # APPLICATION ACTIONS
        ########################################################

        if tool in {
            "OPEN_APP",
            "CLOSE_APP",
        }:

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "app"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "app"
                ] = value

        ########################################################
        # WINDOW ACTIONS
        #
        # Every window executor receives one canonical target:
        #
        #     "window"
        #
        # The model may use window_title, title, app_name, target,
        # etc. The toolset absorbs those naming differences here.
        ########################################################

        if tool in {
            "FOCUS_WINDOW",
            "CLOSE_WINDOW",
            "MINIMIZE_WINDOW",
            "MAXIMIZE_WINDOW",
            "RESTORE_WINDOW",
            "MOVE_WINDOW",
            "RESIZE_WINDOW",
            "TAKE_WINDOW_SCREENSHOT",
        }:

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "window"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "window"
                ] = value

        ########################################################
        # URL ACTIONS
        ########################################################

        if tool == "OPEN_URL":

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "url"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "url"
                ] = value

        ########################################################
        # SEARCH ACTIONS
        ########################################################

        if tool == "SEARCH_WEB":

            value = (
                self._first_value(
                    source,
                    (
                        "query",
                        "search_query",
                        "text",
                        "target",
                        "term",
                    )
                )
            )

            if value is not None:

                normalized[
                    "query"
                ] = value

        ########################################################
        # KEY ACTIONS
        ########################################################

        if tool == "PRESS_KEY":

            value = (
                self._first_value(
                    source,
                    self.PARAMETER_ALIASES[
                        "key"
                    ]
                )
            )

            if value is not None:

                normalized[
                    "key"
                ] = value

        ########################################################
        # WAIT
        ########################################################

        if tool == "WAIT":

            if (
                "seconds"
                not in normalized
            ):

                value = (
                    self._first_value(
                        source,
                        self.PARAMETER_ALIASES[
                            "seconds"
                        ]
                    )
                )

                if value is not None:

                    normalized[
                        "seconds"
                    ] = value

            if (
                "time_ms"
                in source
                and
                "seconds"
                not in normalized
            ):

                try:

                    normalized[
                        "seconds"
                    ] = (
                        float(
                            source[
                                "time_ms"
                            ]
                        )
                        / 1000.0
                    )

                except (
                    TypeError,
                    ValueError
                ):
                    pass

        return normalized

    ############################################################
    # FIRST VALUE
    ############################################################

    @staticmethod
    def _first_value(
        parameters,
        names
    ):

        for name in names:

            if name not in parameters:
                continue

            value = parameters[
                name
            ]

            if value is None:
                continue

            if (
                isinstance(
                    value,
                    str
                )
                and
                not value.strip()
            ):
                continue

            return value

        return None

    ############################################################
    # VALIDATE
    ############################################################

    def validate(
        self,
        tool,
        parameters=None
    ):

        name = (
            self.normalize_tool(
                tool
            )
        )

        params = (
            self.normalize_parameters(
                name,
                parameters or {}
            )
        )

        ########################################################
        # INTERNAL
        ########################################################

        if name in self.INTERNAL:

            return (
                True,
                params,
                ""
            )

        ########################################################
        # UNKNOWN TOOL
        ########################################################

        if name not in self.ACTION_MAP:

            return (
                False,
                params,
                f"Unsupported action: {name}"
            )

        ########################################################
        # REQUIRED PARAMETERS
        ########################################################

        required = {
            ####################################################
            # APPLICATIONS
            ####################################################

            "OPEN_APP": (
                "app",
            ),

            "CLOSE_APP": (
                "app",
            ),

            ####################################################
            # WEB
            ####################################################

            "OPEN_URL": (
                "url",
            ),

            "SEARCH_WEB": (
                "query",
            ),

            ####################################################
            # WINDOWS
            ####################################################

            "FOCUS_WINDOW": (
                "window",
            ),

            "CLOSE_WINDOW": (
                "window",
            ),

            "MINIMIZE_WINDOW": (
                "window",
            ),

            "MAXIMIZE_WINDOW": (
                "window",
            ),

            "RESTORE_WINDOW": (
                "window",
            ),

            "MOVE_WINDOW": (
                "window",
                "x",
                "y",
            ),

            "RESIZE_WINDOW": (
                "window",
                "width",
                "height",
            ),

            ####################################################
            # TEXT / INPUT
            ####################################################

            "TYPE_TEXT": (
                "text",
            ),

            "PRESS_KEY": (
                "key",
            ),

            ####################################################
            # VISION / UI
            ####################################################

            "CLICK_TEXT": (
                "target",
            ),

            "LOCATE_TEXT": (
                "target",
            ),

            "CLICK_TYPE_ENTER": (
                "target",
            ),
        }

        for parameter in required.get(
            name,
            ()
        ):

            if (
                parameter not in params
                or
                params[
                    parameter
                ] is None
            ):

                return (
                    False,
                    params,
                    (
                        f"{name} requires "
                        f"'{parameter}'."
                    )
                )

        ########################################################
        # WINDOW GEOMETRY VALIDATION
        ########################################################

        if name in {
            "MOVE_WINDOW",
            "RESIZE_WINDOW",
        }:

            numeric_parameters = (
                "x",
                "y",
            ) if name == "MOVE_WINDOW" else (
                "width",
                "height",
            )

            for parameter in numeric_parameters:

                try:

                    params[
                        parameter
                    ] = int(
                        params[
                            parameter
                        ]
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    return (
                        False,
                        params,
                        (
                            f"{name} parameter "
                            f"'{parameter}' must be numeric."
                        )
                    )

            if name == "RESIZE_WINDOW":

                if (
                    params["width"] <= 0
                    or
                    params["height"] <= 0
                ):

                    return (
                        False,
                        params,
                        "RESIZE_WINDOW dimensions must be positive."
                    )

        ########################################################
        # WAIT VALIDATION
        ########################################################

        if name == "WAIT":

            if (
                "seconds"
                not in params
            ):

                return (
                    False,
                    params,
                    "WAIT requires seconds."
                )

            try:

                seconds = float(
                    params[
                        "seconds"
                    ]
                )

                if seconds < 0:

                    return (
                        False,
                        params,
                        "WAIT seconds cannot be negative."
                    )

                params[
                    "seconds"
                ] = seconds

            except (
                TypeError,
                ValueError
            ):

                return (
                    False,
                    params,
                    "WAIT seconds must be numeric."
                )

        ########################################################
        # VALID
        ########################################################

        return (
            True,
            params,
            ""
        )

    ############################################################
    # BUILD CORE ACTION
    ############################################################

    def build(
        self,
        tool,
        parameters=None
    ):

        name = (
            self.normalize_tool(
                tool
            )
        )

        valid, params, error = (
            self.validate(
                name,
                parameters
            )
        )

        if not valid:

            return None

        action_type = (
            self.ACTION_MAP.get(
                name
            )
        )

        if action_type is None:

            return None

        return CoreAction(
            action=action_type,
            parameters=params
        )

    ############################################################
    # CORE
    #
    # Compatibility method used by the existing
    # ComputerUseAgent.
    ############################################################

    def core(
        self,
        tool,
        parameters=None
    ):

        return self.build(
            tool,
            parameters
        )

    ############################################################
    # EXECUTE
    #
    # Optional direct execution interface.
    ############################################################

    def execute(
        self,
        tool,
        parameters=None
    ):

        if self.engine is None:

            return {
                "success":
                    False,

                "error":
                    "AutomationEngine is not bound."
            }

        ############################################################
        # BROWSER INTELLIGENCE
        #
        # OPEN_URL and SEARCH_WEB are routed through the
        # deterministic browser layer before the generic
        # AutomationEngine path.
        ############################################################

        normalized_tool = (
            self.normalize_tool(
                tool
            )
        )

        normalized_parameters = (
            self.normalize_parameters(
                normalized_tool,
                parameters or {}
            )
        )

        ############################################################
        # FILESYSTEM MUTATION ROUTING
        #
        # The hardened FilesystemExecutor owns filesystem changes.
        # Keep FileIntelligence discovery and mutation execution
        # separate.
        ############################################################

        filesystem_actions = {
            "CREATE_FILE",
            "CREATE_FOLDER",
            "DELETE_FILE",
            "DELETE_FOLDER",
            "COPY",
            "MOVE",
            "RENAME",
        }

        if normalized_tool in filesystem_actions:

            try:

                core_action = self.core(
                    normalized_tool,
                    normalized_parameters,
                )

                if core_action is None:

                    return {
                        "success":
                            False,

                        "action":
                            normalized_tool,

                        "error":
                            (
                                "Could not build core filesystem "
                                f"action: {normalized_tool}"
                            ),
                    }

                result = self.filesystem.execute(
                    core_action
                )

                if not isinstance(
                    result,
                    dict,
                ):

                    return {
                        "success":
                            bool(result),

                        "action":
                            normalized_tool,

                        "result":
                            result,
                    }

                result.setdefault(
                    "action",
                    normalized_tool,
                )

                return result

            except Exception as exc:

                print(
                    "[AgentToolset] "
                    "Filesystem operation error:",
                    exc
                )

                return {
                    "success":
                        False,

                    "action":
                        normalized_tool,

                    "error":
                        str(exc),
                }

        ############################################################
        # UI TARGET ACTION ROUTING
        #
        # LOCATE_TEXT resolves a semantic target without clicking.
        #
        # CLICK_TEXT first tries UIElementTargeting when the caller
        # provides semantic UI state. Only a safe, unambiguous target
        # with usable bounds is converted into a click action.
        #
        # If no UI state is supplied, fall back to the existing
        # AutomationEngine / vision action path.
        ############################################################

        if normalized_tool in {
            "LOCATE_TEXT",
            "CLICK_TEXT",
        }:

            ui_state = (
                normalized_parameters.get(
                    "ui_state",
                    normalized_parameters.get(
                        "state",
                    )
                )
            )

            target_text = str(
                normalized_parameters.get(
                    "text",
                    normalized_parameters.get(
                        "target",
                        normalized_parameters.get(
                            "query",
                            "",
                        )
                    )
                )
                or
                ""
            ).strip()

            ########################################################
            # Only short-circuit when semantic UI state is actually
            # available. Otherwise the existing engine behavior
            # remains authoritative.
            ########################################################

            if (
                isinstance(
                    ui_state,
                    dict
                )
                and
                target_text
            ):

                try:

                    resolved = (
                        self.resolveUITarget(
                            target_text,
                            state=ui_state,
                            action=(
                                "click"
                                if normalized_tool
                                ==
                                "CLICK_TEXT"
                                else
                                "locate"
                            ),
                        )
                    )

                    if normalized_tool == "LOCATE_TEXT":

                        return {
                            "success":
                                bool(
                                    resolved.get(
                                        "found",
                                        False,
                                    )
                                ),

                            "action":
                                normalized_tool,

                            "resolved":
                                resolved,
                        }

                    ################################################
                    # CLICK_TEXT
                    ################################################

                    if not self.isSafeUITarget(
                        resolved
                    ):

                        return {
                            "success":
                                False,

                            "action":
                                normalized_tool,

                            "error":
                                (
                                    resolved.get(
                                        "reason",
                                        "UI target was not safe or was ambiguous.",
                                    )
                                ),

                            "resolved":
                                resolved,
                        }

                    target = resolved.get(
                        "target",
                        {}
                    )

                    bounds = target.get(
                        "bounds"
                    )

                    x = int(
                        bounds.get(
                            "x",
                            0
                        )
                    )

                    y = int(
                        bounds.get(
                            "y",
                            0
                        )
                    )

                    width = int(
                        bounds.get(
                            "width",
                            0
                        )
                    )

                    height = int(
                        bounds.get(
                            "height",
                            0
                        )
                    )

                    if (
                        width <= 0
                        or
                        height <= 0
                    ):

                        return {
                            "success":
                                False,

                            "action":
                                normalized_tool,

                            "error":
                                "UI target has invalid bounds.",

                            "resolved":
                                resolved,
                        }

                    click_x = (
                        x
                        +
                        (
                            width
                            //
                            2
                        )
                    )

                    click_y = (
                        y
                        +
                        (
                            height
                            //
                            2
                        )
                    )

                    click_action = (
                        self.core(
                            "LEFT_CLICK",
                            {
                                "x":
                                    click_x,

                                "y":
                                    click_y,
                            }
                        )
                    )

                    if click_action is None:

                        return {
                            "success":
                                False,

                            "action":
                                normalized_tool,

                            "error":
                                (
                                    "Could not construct "
                                    "semantic click action."
                                ),
                        }

                    result = (
                        self.engine.executeAction(
                            click_action
                        )
                    )

                    return {
                        "success":
                            result is not False,

                        "action":
                            normalized_tool,

                        "resolved":
                            resolved,

                        "click":
                            {
                                "x":
                                    click_x,

                                "y":
                                    click_y,
                            },

                        "result":
                            result,
                    }

                except Exception as exc:

                    print(
                        "[AgentToolset] "
                        "UI target action error:",
                        exc,
                    )

                    return {
                        "success":
                            False,

                        "action":
                            normalized_tool,

                        "error":
                            str(exc),
                    }

        if normalized_tool in {
            "OPEN_URL",
            "SEARCH_WEB",
        }:

            try:

                if normalized_tool == "OPEN_URL":

                    success = (
                        self.browser.open_url(
                            normalized_parameters.get(
                                "url",
                                ""
                            ),
                            browser=(
                                normalized_parameters.get(
                                    "browser"
                                )
                            ),
                        )
                    )

                else:

                    query = (
                        normalized_parameters.get(
                            "query",
                            normalized_parameters.get(
                                "search_query",
                                normalized_parameters.get(
                                    "text",
                                    ""
                                )
                            )
                        )
                    )

                    engine = str(
                        normalized_parameters.get(
                            "engine",
                            "google"
                        )
                        or
                        "google"
                    ).strip().lower()

                    browser = (
                        normalized_parameters.get(
                            "browser"
                        )
                    )

                    if engine == "youtube":

                        success = (
                            self.browser.search_youtube(
                                query,
                                browser=browser,
                            )
                        )

                    else:

                        success = (
                            self.browser.search(
                                query,
                                engine=engine,
                                browser=browser,
                            )
                        )

                return {
                    "success":
                        bool(
                            success
                        ),

                    "action":
                        normalized_tool,

                    "result":
                        (
                            "Browser operation dispatched."
                            if success
                            else
                            "Browser operation failed."
                        ),
                }

            except Exception as exc:

                print(
                    "[AgentToolset] "
                    "Browser operation error:",
                    exc
                )

                return {
                    "success":
                        False,

                    "action":
                        normalized_tool,

                    "error":
                        str(exc),
                }

        action = self.build(
            tool,
            parameters
        )

        if action is None:

            return {
                "success":
                    False,

                "error":
                    (
                        "Invalid or unsupported "
                        f"action: {tool}"
                    )
            }

        try:

            result = (
                self.engine.executeAction(
                    action
                )
            )

            return {
                "success":
                    result is not False,

                "result":
                    result
            }

        except Exception as exc:

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

    ############################################################
    # EXECUTE ACTION
    ############################################################

    def execute_action(
        self,
        action
    ):

        if self.engine is None:

            return {
                "success":
                    False,

                "error":
                    "AutomationEngine is not bound."
            }

        if action is None:

            return {
                "success":
                    False,

                "error":
                    "No action supplied."
            }

        try:

            result = (
                self.engine.executeAction(
                    action
                )
            )

            return {
                "success":
                    result is not False,

                "result":
                    result
            }

        except Exception as exc:

            return {
                "success":
                    False,

                "error":
                    str(exc)
            }

    ############################################################
    # BATCH BUILD
    #
    # Used when another layer wants to prepare several
    # deterministic actions.
    #
    # The autonomous brain can still choose to execute only
    # one action after visual observation.
    ############################################################

    def build_batch(
        self,
        actions: Iterable
    ):

        result = []

        if actions is None:
            return result

        for item in actions:

            if not isinstance(
                item,
                dict
            ):
                continue

            tool = item.get(
                "tool",
                ""
            )

            parameters = item.get(
                "parameters",
                {}
            )

            action = self.build(
                tool,
                parameters
            )

            if action is not None:

                result.append(
                    action
                )

        return result

    ############################################################
    # EXECUTE BATCH
    ############################################################

    def execute_batch(
        self,
        actions: Iterable
    ):

        results = []

        if actions is None:
            return results

        for item in actions:

            if isinstance(
                item,
                CoreAction
            ):

                results.append(
                    self.execute_action(
                        item
                    )
                )

                continue

            if isinstance(
                item,
                dict
            ):

                results.append(
                    self.execute(
                        item.get(
                            "tool",
                            ""
                        ),

                        item.get(
                            "parameters",
                            {}
                        )
                    )
                )

        return results

    ############################################################
    # UI TARGET RESOLUTION
    ############################################################

    def resolveUITarget(
        self,
        target,
        state=None,
        action="click",
    ):

        try:

            return self.ui_targeting.resolve(
                target,
                action=action,
                state=state,
            )

        except Exception as exc:

            print(
                "[AgentToolset] "
                "UI target resolution error:",
                exc,
            )

            return {
                "found":
                    False,

                "target":
                    None,

                "candidates":
                    [],

                "ambiguous":
                    False,

                "reason":
                    str(exc),
            }

    ############################################################
    # UI TARGET SAFETY
    ############################################################

    def isSafeUITarget(
        self,
        result,
    ):

        try:

            return self.ui_targeting.is_safe_target(
                result
            )

        except Exception:

            return False

    ############################################################
    # MODEL CONTEXT
    ############################################################

    def modelContext(
        self
    ):

        browser_state = {}

        try:

            browser_state = (
                self.browser.current_state()
            )

        except Exception:

            browser_state = {}

        return {
            "ui_targeting":
                {
                    "capabilities": [
                        "resolve_text",
                        "resolve_role",
                        "confidence",
                        "ambiguity_detection",
                        "semantic_locate",
                        "semantic_click",
                    ]
                },

            "filesystem":
                {
                    "operations": [
                        "CREATE_FILE",
                        "CREATE_FOLDER",
                        "DELETE_FILE",
                        "DELETE_FOLDER",
                        "COPY",
                        "MOVE",
                        "RENAME",
                    ]
                },

            "tools":
                self.available(),

            "browser":
                browser_state,

            "internal":
                sorted(
                    self.INTERNAL
                ),

            "parameter_aliases":
                {
                    key:
                        list(
                            values
                        )

                    for key, values
                    in self.PARAMETER_ALIASES.items()
                }
        }

    ############################################################
    # COMPATIBILITY ALIASES
    ############################################################

    def model_context(
        self
    ):

        return self.modelContext()

    def buildCoreAction(
        self,
        tool,
        parameters=None
    ):

        return self.build(
            tool,
            parameters
        )

    def executeAction(
        self,
        tool,
        parameters=None
    ):

        return self.execute(
            tool,
            parameters
        )