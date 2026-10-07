from __future__ import annotations

import re

from collections import deque
from dataclasses import dataclass
from typing import Optional

from ai.local_client import LocalAIClient
from backend.local_responder import LocalResponder
from backend.local_tool_registry import LocalToolRegistry, LocalToolResult
from backend.core_local_capabilities import register_core_local_tools


@dataclass
class BrainResponse:

    mode: str = "CHAT"

    answer: str = ""

    computer_goal: str = ""

    reasoning: str = ""

    success: bool = True

    error: str = ""


class AIBrain:

    """
    JARVIS X
    LOCAL-FIRST UNIVERSAL BRAIN

    This is the high-level intelligence layer of JARVIS.

    Architecture:

        FAST LOCAL RESPONDER
                |
                v
        LOCAL CAPABILITIES
                |
                v
        LOCAL GENERAL BRAIN
                |
        explicit computer request?
             /       \
           NO         YES
           |           |
           v           v
        ANSWER     COMPUTER AGENT

    IMPORTANT:

    - No Gemini client is used here.
    - No cloud AI routing is performed here.
    - All non-computer intelligence stays local.
    - Physical computer work is handed to ComputerUseAgent.
    - This class does not execute computer actions.

    HYBRID is retained as a compatibility mode because the
    current AIController still knows about that mode. The local
    brain itself does not need to emit HYBRID at this stage.
    """

    CHAT = "CHAT"

    COMPUTER = "COMPUTER"

    HYBRID = "HYBRID"

    VALID_MODES = {
        CHAT,
        COMPUTER,
        HYBRID,
    }

    ############################################################
    # INITIALIZATION
    ############################################################

    def __init__(
        self,
        local_client: Optional[LocalAIClient] = None,
        local_responder: Optional[LocalResponder] = None,
        tool_registry: Optional[LocalToolRegistry] = None,
    ):

        self.local = (
            local_client
            if local_client is not None
            else LocalAIClient()
        )

        self.localResponder = (
            local_responder
            if local_responder is not None
            else LocalResponder()
        )

        ########################################################
        # UNIVERSAL LOCAL CAPABILITY REGISTRY
        ########################################################

        self.tools = (
            tool_registry
            if tool_registry is not None
            else register_core_local_tools(
                LocalToolRegistry()
            )
        )

        self.last_request = ""

        self.last_response: Optional[
            BrainResponse
        ] = None

        ########################################################
        # SHORT-TERM CONVERSATION MEMORY
        #
        # Keep only a bounded number of recent turns. This gives
        # the local model continuity without growing the prompt
        # forever.
        ########################################################

        self._conversation = deque(
            maxlen=12
        )

        self.context_turn_limit = 6

        print(
            "[AIBrain] "
            "LOCAL JARVIS BRAIN READY."
        )

        print(
            "[AIBrain] "
            f"Local model: "
            f"{getattr(self.local, 'model', 'unknown')}"
        )

        print(
            "[AIBrain] "
            "Gemini is NOT part of this brain."
        )

    ############################################################
    # THINK
    ############################################################

    def think(
        self,
        request,
    ) -> BrainResponse:

        request = str(
            request or ""
        ).strip()

        self.last_request = request

        if not request:

            response = BrainResponse(
                mode=self.CHAT,
                answer="",
            )

            self.last_response = response

            return response

        ########################################################
        # COMPUTER FIRST
        #
        # Explicit physical-computer requests are immediately
        # handed to the ComputerUseAgent by AIController.
        ########################################################

        if self._is_computer_request(
            request
        ):

            response = BrainResponse(
                mode=self.COMPUTER,
                answer="",
                computer_goal=request,
                reasoning=(
                    "The user explicitly requested "
                    "physical computer interaction."
                ),
            )

            self.last_response = response

            print(
                "[AIBrain] Mode: COMPUTER"
            )

            return response

        ########################################################
        # FAST LOCAL RESPONDER
        ########################################################

        try:

            local_response = (
                self.localResponder.respond(
                    request
                )
            )

        except Exception as exc:

            print(
                "[AIBrain] LocalResponder warning:",
                exc
            )

            local_response = None

        if local_response:

            response = BrainResponse(
                mode=self.CHAT,
                answer=str(
                    local_response
                ).strip(),
                reasoning=(
                    "Handled by the deterministic "
                    "local responder."
                ),
            )

            self.last_response = response

            print(
                "[AIBrain] Mode: CHAT"
            )

            print(
                "[AIBrain] Source: FAST LOCAL"
            )

            return response

        ########################################################
        # UNIVERSAL LOCAL CAPABILITY REGISTRY
        ########################################################

        try:

            tool_result = (
                self.tools.execute(
                    request
                )
            )

        except Exception as exc:

            print(
                "[AIBrain] Local capability error:",
                exc
            )

            tool_result = LocalToolResult(
                handled=False,
                metadata={
                    "error": str(exc),
                },
            )

        if (
            isinstance(
                tool_result,
                LocalToolResult,
            )
            and
            tool_result.handled
            and
            str(
                tool_result.answer
                or ""
            ).strip()
        ):

            response = BrainResponse(
                mode=self.CHAT,
                answer=str(
                    tool_result.answer
                ).strip(),
                reasoning=(
                    "Handled by local capability: "
                    f"{tool_result.tool or 'unknown'}."
                ),
            )

            self.last_response = response

            print(
                "[AIBrain] Mode: CHAT"
            )

            print(
                "[AIBrain] Source: LOCAL TOOL"
            )

            print(
                "[AIBrain] Tool:",
                tool_result.tool or "unknown",
            )

            return response

        ########################################################
        # GENERAL LOCAL LANGUAGE BRAIN
        ########################################################

        response = (
            self._ask_local_brain(
                request
            )
        )

        if response is None:

            response = BrainResponse(
                mode=self.CHAT,
                answer="",
                success=False,
                error=(
                    "Local brain returned no usable response."
                ),
            )

        self.last_response = response

        print(
            "[AIBrain] Mode:",
            response.mode
        )

        print(
            "[AIBrain] Source:",
            "LOCAL MODEL"
            if response.success
            else "LOCAL MODEL ERROR"
        )

        return response

    ############################################################
    # LOCAL GENERAL BRAIN
    ############################################################

    def _ask_local_brain(
        self,
        request,
    ) -> Optional[BrainResponse]:

        try:

            answer = self.local.chat(
                self._build_context_prompt(
                    request
                ),
                system=self._system_prompt(),
            )

        except Exception as exc:

            print(
                "[AIBrain] "
                f"Local AI error: {exc}"
            )

            return BrainResponse(
                mode=self.CHAT,
                answer="",
                success=False,
                error=str(exc),
            )

        answer = str(
            answer or ""
        ).strip()

        if not answer:

            return BrainResponse(
                mode=self.CHAT,
                answer="",
                success=False,
                error=(
                    "Local AI returned an empty response."
                ),
            )

        ########################################################
        # The local language model returns human-facing text,
        # not routing JSON.
        ########################################################

        response = BrainResponse(
            mode=self.CHAT,
            answer=answer,
            reasoning=(
                "Handled by the local general-purpose "
                "language model."
            ),
        )

        self._remember_turn(
            request,
            answer,
        )

        return response

    ############################################################
    # LOCAL SYSTEM PROMPT
    ############################################################

    @staticmethod
    def _system_prompt():

        return """
You are JARVIS X, a highly capable local personal assistant.

Your job is to understand the user's intent and respond like an
intelligent human assistant, while remaining accurate, calm,
concise, and useful.

============================================================
CORE BEHAVIOR
============================================================

Think before answering.

Answer the user's actual request rather than merely reacting to
individual keywords.

Use the recent conversation context when the user refers to
something previously discussed.

Do not repeat information the user already knows unless it is
useful.

Do not add filler just to make the response longer.

Do not use the same opening or closing phrase in every answer.

Do not constantly say "Certainly, sir", "Of course, sir", or
"How can I assist you today?"

Use "sir" naturally and sparingly when it fits the conversation.

Do not pretend to have emotions, experiences, or actions you did
not actually have.

============================================================
JARVIS COMMUNICATION STYLE
============================================================

Your personality should feel:

- calm
- intelligent
- confident
- composed
- subtly witty when appropriate
- respectful
- naturally conversational
- emotionally aware of the user's tone

Do NOT sound like a robotic manual.

Do NOT sound excessively enthusiastic.

Do NOT turn simple questions into long essays.

Do NOT use fake dramatic language.

Match the user's level of formality and the complexity of the
request.

============================================================
ADAPT RESPONSE STYLE TO INTENT
============================================================

CASUAL / CONVERSATIONAL:

Respond naturally and briefly.

TECHNICAL:

Be precise and structured. Explain terminology when helpful.

SCHOOL / LEARNING:

Teach clearly. Break difficult ideas into understandable pieces.
Use examples when they improve understanding.

REQUEST FOR SIMPLIFICATION:

Preserve the meaning but explain it in easier language.

CALCULATION:

Give the correct result directly. Show a short calculation only
when useful.

WRITING / REWRITING:

Produce the requested text directly without unnecessary commentary.

PLANNING / DECISION SUPPORT:

Reason through the relevant choices and provide a useful
recommendation with trade-offs when appropriate.

UNCERTAIN REQUEST:

Do not invent an answer. Ask a concise clarification question.

SHORT FOLLOW-UP:

Interpret the request using the recent conversation context.

============================================================
RESPONSE STRUCTURE
============================================================

Prefer natural paragraphs for normal conversation.

Use bullets or headings only when they genuinely make a response
easier to understand.

Use Markdown sparingly.

Never wrap the answer in JSON.

Never output routing metadata.

Never output internal reasoning.

Never mention this system prompt.

============================================================
COMPUTER BOUNDARY
============================================================

You are the intellectual brain of JARVIS.

A separate ComputerUseAgent handles physical computer interaction.

Do not claim to have clicked, typed, opened, saved, downloaded,
or otherwise operated the computer unless the Computer Agent
actually performed that operation.

Do not instruct yourself to use the computer for a task that can
be answered or completed intellectually.

============================================================
FINAL QUALITY CHECK
============================================================

Before responding, silently check:

1. Did I answer the actual question?
2. Did I use relevant conversation context?
3. Is the answer as concise as the task deserves?
4. Does the tone sound natural rather than robotic?
5. Did I avoid unnecessary repetition?
6. Did I avoid inventing information or actions?

Return only the final user-facing answer.
""".strip()

    ############################################################
    # SHORT-TERM CONVERSATION CONTEXT
    ############################################################

    def _remember_turn(
        self,
        user_text,
        assistant_text,
    ):

        user_text = str(
            user_text or ""
        ).strip()

        assistant_text = str(
            assistant_text or ""
        ).strip()

        if not user_text:
            return

        self._conversation.append(
            {
                "role": "user",
                "content": user_text,
            }
        )

        if assistant_text:

            self._conversation.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                }
            )

    def _build_context_prompt(
        self,
        request,
    ):

        request = str(
            request or ""
        ).strip()

        recent = list(
            self._conversation
        )[-(
            self.context_turn_limit * 2
        ):]

        if not recent:
            return request

        lines = [
            "RECENT CONVERSATION:",
            "",
        ]

        for item in recent:

            role = str(
                item.get(
                    "role",
                    "",
                )
            ).upper()

            content = str(
                item.get(
                    "content",
                    "",
                )
            ).strip()

            if not content:
                continue

            lines.append(
                f"{role}: {content}"
            )

        lines.extend(
            [
                "",
                "CURRENT REQUEST:",
                request,
            ]
        )

        return "\n".join(
            lines
        )

    def conversation_context(
        self,
    ):

        return list(
            self._conversation
        )

    def clear_context(
        self,
    ):

        self._conversation.clear()

    ############################################################
    ############################################################
    # COMPUTER REQUEST DETECTION
    ############################################################

    @staticmethod
    def _is_computer_request(
        request,
    ) -> bool:

        """
        Decide whether the user's request requires physical
        interaction with the computer.

        IMPORTANT:
        This is routing only.

        It does not execute anything and it does not know how
        the computer task will be performed.

        The rule is intentionally broader than a hard-coded
        application list. Requests such as:

            open YouTube
            open Spotify
            launch VS Code
            start Discord
            close Chrome
            open File Explorer
            play a Minecraft tutorial on YouTube
            search Google for Python tutorials
            type this into Notepad
            save the file
            move this PDF
            rename this folder

        must reach COMPUTER mode even when the application or
        website name is not present in a fixed list.
        """

        text = str(
            request or ""
        ).strip().lower()

        if not text:

            return False

        ########################################################
        # 1. Explicit computer language
        ########################################################

        explicit_phrases = (
            "use the computer",
            "using the computer",
            "control the computer",
            "take control of the computer",
            "on my computer",
            "on my pc",
            "on my laptop",
            "on my desktop",
            "with my keyboard",
            "with my mouse",
            "on the screen",
            "on screen",
            "on my screen",
            "in my browser",
            "in chrome",
            "in edge",
            "in opera",
            "in firefox",
        )

        if any(
            phrase in text
            for phrase in explicit_phrases
        ):

            return True

        ########################################################
        # 2. Explicit URL / domain navigation
        ########################################################

        url_patterns = (
            r"\bhttps?://",
            r"\bwww\.",
            r"\b[a-z0-9-]+\.(?:com|in|org|net|io|ai|dev|co|tv)\b",
        )

        if any(
            re.search(
                pattern,
                text,
            )
            for pattern in url_patterns
        ):

            physical_navigation_verbs = (
                "open",
                "go to",
                "visit",
                "launch",
                "navigate",
                "browse",
                "load",
            )

            if any(
                verb in text
                for verb in physical_navigation_verbs
            ):

                return True

        ########################################################
        # 3. Window-management language
        #
        # Natural phrases such as:
        #   bring Opera to the front
        #   make Opera active
        #   put Opera in front
        #   switch to Opera
        #   bring the browser forward
        #
        # are physical computer requests even when the literal
        # word "focus" is not present.
        ########################################################

        window_management_patterns = (
            r"\bbring\b.+\bto\s+the\s+front\b",
            r"\bbring\b.+\bto\s+front\b",
            r"\bbring\b.+\bforward\b",
            r"\bbring\s+(the\s+)?(?:window|browser|app|application)\b.+\bfront\b",
            r"\bput\b.+\bin\s+front\b",
            r"\bput\b.+\bto\s+the\s+front\b",
            r"\bmake\b.+\bthe\s+active\s+window\b",
            r"\bmake\b.+\bactive\b",
            r"\bactivate\b.+\bwindow\b",
            r"\bactivate\b.+\bapp\b",
            r"\bswitch\s+to\b.+",
            r"\bswitch\s+over\s+to\b.+",
            r"\bswitch\s+back\s+to\b.+",
            r"\bfocus\s+on\b.+",
            r"\bfocus\b.+\bwindow\b",
        )

        if any(
            re.search(
                pattern,
                text,
            )
            for pattern in window_management_patterns
        ):

            return True

        ########################################################
        # 4. Application / website actions
        #
        # The target is deliberately NOT a fixed application list.
        # This allows arbitrary app names to reach the computer
        # agent.
        ########################################################

        app_verbs = (
            "open",
            "launch",
            "start",
            "close",
            "quit",
            "exit",
            "restart",
            "minimize",
            "maximize",
            "restore",
            "focus",
        )

        if any(
            re.search(
                rf"\b{re.escape(verb)}\b",
                text,
            )
            for verb in app_verbs
        ):

            ####################################################
            # Avoid obvious non-computer language uses of "open".
            ####################################################

            non_computer_open_patterns = (
                r"^open\s+(a|an|the)?\s*(question|discussion|conversation|debate)",
                r"^open\s+(source|ended?)",
                r"\bopen\s+to\s+(ideas|suggestions|discussion)",
                r"\bopen\s+the\s+(book|chapter|topic|subject)\b",
            )

            if not any(
                re.search(
                    pattern,
                    text,
                )
                for pattern in non_computer_open_patterns
            ):

                return True

        ########################################################
        # 4. Direct physical interaction verbs
        ########################################################

        physical_action_patterns = (
            r"\bclick\b",
            r"\bdouble[- ]?click\b",
            r"\bright[- ]?click\b",
            r"\btype\b",
            r"\bpress\b",
            r"\bhold\b",
            r"\brelease\b",
            r"\bpaste\b",
            r"\bscroll\b",
            r"\bdrag\b",
            r"\bmove\s+(the\s+)?mouse\b",
            r"\bmove\s+the\s+window\b",
            r"\bresize\s+(the\s+)?window\b",
            r"\bscreenshot\b",
            r"\bcapture\s+(the\s+)?screen\b",
            r"\bcopy\b",
            r"\brename\b",
            r"\bdelete\b",
            r"\bmove\b",
            r"\bsave\b",
            r"\bdownload\b",
            r"\bupload\b",
            r"\bcreate\s+(a\s+)?file\b",
            r"\bcreate\s+(a\s+)?folder\b",
        )

        if any(
            re.search(
                pattern,
                text,
            )
            for pattern in physical_action_patterns
        ):

            return True

        ########################################################
        # 5. Website / media intent
        #
        # This covers cases such as:
        #
        #   play Minecraft tutorial on YouTube
        #   search YouTube for redstone tutorial
        #   watch a video on YouTube
        #
        # These are physical browser tasks, not normal chat.
        ########################################################

        web_targets = (
            "youtube",
            "google",
            "bing",
            "reddit",
            "instagram",
            "facebook",
            "x.com",
            "twitter",
            "spotify",
            "netflix",
            "amazon",
            "github",
            "linkedin",
            "gmail",
            "drive",
            "discord",
        )

        web_action_verbs = (
            "open",
            "go to",
            "visit",
            "search",
            "find",
            "play",
            "watch",
            "listen",
            "download",
            "upload",
            "post",
            "message",
            "send",
            "check",
            "browse",
            "navigate",
        )

        has_web_target = any(
            re.search(
                rf"\b{re.escape(target)}\b",
                text,
            )
            for target in web_targets
        )

        has_web_action = any(
            re.search(
                rf"\b{re.escape(action)}\b",
                text,
            )
            for action in web_action_verbs
        )

        if (
            has_web_target
            and
            has_web_action
        ):

            return True

        ########################################################
        # 6. Explicit browser searching
        ########################################################

        browser_search_patterns = (
            r"^search\s+.+\s+on\s+(google|youtube|bing)$",
            r"^search\s+(google|youtube|bing)\s+for\s+.+$",
            r"^find\s+.+\s+on\s+(google|youtube|bing)$",
            r"^look\s+up\s+.+\s+on\s+(google|youtube|bing)$",
            r"^play\s+.+\s+on\s+youtube$",
            r"^watch\s+.+\s+on\s+youtube$",
            r"^listen\s+to\s+.+\s+on\s+spotify$",
        )

        if any(
            re.fullmatch(
                pattern,
                text,
            )
            for pattern in browser_search_patterns
        ):

            return True

        ########################################################
        # 7. File / folder references
        #
        # These are computer tasks when a physical operation is
        # requested. The detector does not need to know the actual
        # filename.
        ########################################################

        file_terms = (
            "file",
            "folder",
            "directory",
            "pdf",
            "document",
            "spreadsheet",
            "excel file",
            "word file",
            "photo",
            "image",
            "video",
            "desktop",
            "recycle bin",
            "downloads folder",
        )

        file_actions = (
            "open",
            "find",
            "locate",
            "search",
            "move",
            "copy",
            "rename",
            "delete",
            "save",
            "create",
            "download",
            "upload",
        )

        has_file_term = any(
            term in text
            for term in file_terms
        )

        has_file_action = any(
            re.search(
                rf"\b{re.escape(action)}\b",
                text,
            )
            for action in file_actions
        )

        if (
            has_file_term
            and
            has_file_action
        ):

            return True

        ########################################################
        # 8. Keyboard / mouse combinations
        ########################################################

        input_terms = (
            "keyboard",
            "mouse",
            "hotkey",
            "shortcut",
        )

        if any(
            term in text
            for term in input_terms
        ):

            return True

        ########################################################
        # 9. Nothing indicates physical interaction.
        #
        # Keep the request in CHAT so the local language brain
        # can handle it normally.
        ########################################################

        return False

    ############################################################
    # LOCAL TOOL REGISTRY
    ############################################################

    def register_tool(
        self,
        tool,
    ):

        return self.tools.register(
            tool
        )

    def unregister_tool(
        self,
        name,
    ):

        return self.tools.unregister(
            name
        )

    def local_tools(
        self,
    ):

        return self.tools.tools()

    ############################################################
    ############################################################
    # LAST RESPONSE
    ############################################################

    def last(
        self,
    ):

        return self.last_response

    ############################################################
    # RESET
    ############################################################

    def reset(
        self,
    ):

        self.last_request = ""

        self.last_response = None

        self.clear_context()

    ############################################################
    # REPRESENTATION
    ############################################################

    def __repr__(
        self,
    ):

        mode = getattr(
            self.last_response,
            "mode",
            None,
        )

        model = getattr(
            self.local,
            "model",
            None,
        )

        return (
            "<AIBrain "
            f"model={model!r} "
            f"tools={len(self.tools)} "
            f"context={len(self._conversation)} "
            f"last_mode={mode!r}>"
        )