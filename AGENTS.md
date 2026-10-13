# Repository guidance for coding assistants

## Project overview
JARVIS X is a modular Python desktop AI agent. Its documented capabilities include conversational AI, voice interaction, computer automation, vision/OCR, memory, business discovery, task orchestration, and a PySide6 interface.

## Working rules
- Read the relevant implementation and its callers before proposing or making a change. Follow the existing architecture and conventions; do not rewrite unrelated modules.
- Prefer small, focused changes with clear reasons. Preserve existing behavior unless the task explicitly asks to change it.
- Do not claim a test, command, desktop interaction, or deployment succeeded unless it was actually run and its result was observed.
- Never commit secrets, API keys, tokens, personal data, local environment files, or machine-specific paths. Use environment variables and update `.env.example` only with placeholder names and safe descriptions.
- Treat computer-control, terminal, file-system, keyboard, mouse, and clipboard actions as potentially destructive. Preserve user confirmation and cancellation safeguards; do not weaken security boundaries to make a demo work.
- Keep long-running AI, network, and automation tasks from blocking the Qt UI thread. Respect the existing worker-thread, cancellation, and stale-result handling patterns.
- Handle unavailable AI providers, permissions, network errors, missing optional dependencies, and malformed model output explicitly. Avoid silently reporting success after a failed action.
- For URL/business discovery and other external-data features, validate inputs, handle timeouts and rate limits, and explain uncertainty rather than inventing results.
- Add or update tests for behavior changes when a suitable test framework exists. Include failure paths and regression cases, not only happy paths.
- Before finalizing, run the narrowest relevant tests and any applicable static/syntax checks. State exactly what was and was not verified.

## Developer environment and response style
- The project is developed on Windows with VS Code. Prefer PowerShell commands when giving local instructions.
- The project owner may apply changes manually. When asked for instructions, provide exact file paths, complete replacement code or precise patches, and commands in execution order.
- When making changes directly through GitHub, work on a feature branch and propose a pull request. Do not merge into `main` unless explicitly authorized.
- Keep documentation consistent with the implementation. Do not assume README claims prove that a feature is implemented or tested; inspect the code.

## Repository map
Use the current tree as the source of truth. The README documents these main areas:
- `ai/`: AI routing, tools, and validation
- `automation/`: computer and workflow automation
- `backend/`: agent planning and orchestration
- `business_outreach/`: business discovery and lead workflows
- `core/`: core runtime and goal management
- `database/`: persistence
- `jarvis_tests/`: tests
- `memory/`: memory and context
- `services/`: integrations
- `ui/`: PySide6 interface
- `vision/`: screen analysis
- `voice/`: speech input and output
