# JARVIS X

> A modular desktop AI agent combining conversational AI, voice interaction, computer automation, memory, vision, and business discovery.

![JARVIS X](jarvis_screen.png)

## Overview

**JARVIS X** is a Python-based desktop AI-agent project designed as a modular system rather than a single chatbot.

The application combines an AI reasoning layer with voice interaction, computer-use automation, memory, vision, business discovery, and a custom PySide6 interface.

The goal of the project is to explore how multiple AI capabilities can be orchestrated into a single desktop agent that can understand requests, plan tasks, interact with the computer, and provide useful information through different interfaces.

---

## Key Capabilities

### AI Assistant

- Natural-language command processing
- AI request understanding and routing
- Tool-based task execution
- Chat, computer, and hybrid execution modes
- Centralized AI controller
- Task orchestration

### Voice Interaction

- Voice command input
- Wake-word activation
- Voice-controlled interaction
- Text-to-speech responses
- Voice interruption handling

### Computer Automation

JARVIS X can interact with the local computer through modular automation components including:

- Application control
- File and folder operations
- Keyboard control
- Mouse control
- Window management
- Clipboard operations
- Terminal commands
- Screenshots
- OCR
- System controls
- Computer-use task execution

### Vision

The vision subsystem supports capabilities such as:

- Screen analysis
- UI element detection
- Text localization
- OCR
- Visual interaction
- Computer-use visual assistance

### Memory

JARVIS X contains a dedicated memory subsystem for:

- Conversation context
- Persistent memory
- Memory retrieval
- Context injection
- Memory lifecycle management

### Business Discovery

JARVIS X also contains a business-discovery and lead-management subsystem.

A user can define requirements such as:

```text
Find dentists in Noida

or:
Find local businesses in Sector 137
that have a weak or missing web presence.

The system can then support:
- Business discovery
- Lead qualification
- Website verification
- Lead scoring
- Lead tracking
- Search-provider integrations
- Outreach workflow support
User Interface
The application uses a custom PySide6 desktop interface inspired by a JARVIS-style HUD.
The interface includes:
- AI status
- System telemetry
- AI console
- Voice visualization
- Animated HUD components
- Analytics dashboard
- Command-center workspace
Architecture
At the center of JARVIS X is a modular controller and task-orchestration architecture.
                             USER
                               │
                     ┌─────────┴─────────┐
                     │                   │
                   Voice                Text
                     │                   │
                     └─────────┬─────────┘
                               │
                               ▼
                         MainWindow
                               │
                               ▼
                         AIController
                               │
                               ▼
                            AIBrain
                      ┌────────┼────────┐
                      │        │        │
                     CHAT   COMPUTER   HYBRID
                               │
                               ▼
                       TaskOrchestrator
                               │
                               ▼
                       ComputerUseAgent
                               │
                               ▼
                       AutomationEngine
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
           Vision            Voice            Memory
             │                                   │
             └─────────────────┬─────────────────┘
                               │
                               ▼
                     Business Discovery

Core Engineering Concepts
JARVIS X uses several architectural patterns to keep the system modular.
Central AI Controller
AIController acts as the bridge between the user-facing interface, AI reasoning, voice, task execution, and computer-control capabilities.
Task Orchestration
Computer tasks are represented and managed through a task-orchestration layer rather than being executed directly from the UI.
Asynchronous Execution
Long-running commands are moved into Qt worker threads so that the graphical interface can remain responsive during AI or automation tasks.
Execution Invalidation
Commands receive execution identifiers. When a task is interrupted, stale results can be rejected when they return later.
Interrupt and Cancellation Handling
Users can interrupt active tasks through text or voice commands, and the system attempts to stop speech and cancel the active task.
Modular Subsystems
Major capabilities are separated into dedicated modules for:
- AI
- Automation
- Memory
- Voice
- Vision
- Business Discovery
- UI
- Services
- Testing
Project Structure
JARVIS-X/
│
├── ai/                       # AI routing, tools and validation
│
├── automation/               # Computer and workflow automation
│   ├── executors/
│   ├── clipboard/
│   ├── keyboard/
│   ├── mouse/
│   ├── ocr/
│   ├── screenshot/
│   ├── services/
│   └── vision/
│
├── backend/                  # Agent, planning and orchestration logic
│
├── business_outreach/        # Business discovery and lead workflows
│   ├── database/
│   ├── discovery/
│   ├── models/
│   ├── outreach/
│   ├── qualification/
│   ├── samples/
│   └── workflow/
│
├── core/                     # Core runtime and goal management
│
├── database/                 # Persistent storage implementation
│
├── jarvis_tests/             # Automated and integration tests
│
├── memory/                   # Memory and context subsystem
│
├── models/                   # Model configuration/documentation
│
├── resources/                # Application assets
│
├── scripts/                  # Development utilities
│
├── services/                 # External/service integrations
│
├── ui/                       # PySide6 user interface
│   ├── components/
│   └── themes/
│
├── vision/                   # Vision and screen-analysis subsystem
│
├── voice/                    # Speech recognition, wake detection and TTS
│
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment-variable template
└── .gitignore                # Repository exclusions

Technology Stack
Area	Technology
Language	Python
Desktop UI	PySide6 / Qt
AI	AI/LLM integrations
Computer Automation	Python automation modules
Computer Vision	Vision / OCR tooling
Speech	Speech recognition + TTS
Storage	SQLite
Testing	Pytest
API Integrations	Environment-configured external services


Getting Started
1. Clone the repository
git clone https://github.com/aaravpachouri/JARVIS-X.git
cd JARVIS-X

2. Create a virtual environment
Windows PowerShell:
python -m venv .venv

3. Activate the environment
.venv\Scripts\Activate.ps1

4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

5. Configure environment variables
Create a local .env file from .env.example.
For example:
.env.example
     ↓
.env

Add the credentials required by the integrations you choose to use.
Never commit .env or API keys to GitHub.
6. Run JARVIS X
python main.py

Screenshots
Main HUD

Agent Interface

Example Interactions
Business Discovery
User
  ↓
"Find salons in Noida without a decent website."
  ↓
JARVIS AI reasoning
  ↓
Business discovery
  ↓
Website qualification
  ↓
Lead scoring
  ↓
Results

Computer Automation
User
  ↓
"Open my browser and search for ..."
  ↓
AI reasoning
  ↓
Computer task
  ↓
Task orchestration
  ↓
Computer-use automation

Safety and Permissions
JARVIS X contains computer-control capabilities that can interact with the local machine.
Because automation can perform real actions, users should review commands and permissions carefully before executing tasks.
The project does not claim that computer automation is completely safe or error-free.
Privacy
JARVIS X may maintain local application state and persistent memory.
Local runtime databases and environment files are intentionally excluded from the public repository.
API credentials should be supplied through environment variables rather than stored in source code.
Third-Party Components
JARVIS X may use open-source libraries, models, and other external components.
Third-party software remains subject to its respective license and attribution requirements.
Downloaded model weights and bundled third-party source are intentionally excluded from this repository unless redistribution rights have been verified.
Current Status
Work in Progress
JARVIS X is an evolving personal AI-agent project.
The architecture, models, integrations, automation capabilities, and user interface are actively being improved.
Current development areas include:
- More reliable agent planning
- Better task verification
- Improved computer-use reliability
- Stronger memory and context handling
- Improved vision capabilities
- Better voice interaction
- Expanded business intelligence workflows
- More local AI capabilities
- Better testing and reproducibility
- Reduced dependency on unnecessary external services
Roadmap
Phase 1 — Core Agent
- [x] Modular AI controller
- [x] Chat execution
- [x] Computer task execution
- [x] Voice interaction
- [x] Task orchestration
Phase 2 — Intelligence
- [x] Memory subsystem
- [x] Vision subsystem
- [x] Business discovery
- [x] Task interruption
- [x] Runtime state tracking
Phase 3 — Reliability
- [ ] Expanded automated test coverage
- [ ] Better task verification
- [ ] Improved failure recovery
- [ ] Better observability
- [ ] Cleaner dependency management
Phase 4 — Local AI
- [ ] Expand local-model support
- [ ] Reduce unnecessary external API dependency
- [ ] Improve local inference
- [ ] Explore smaller specialized models
Why I Built JARVIS X
JARVIS X is an exploration of how a desktop AI system can combine multiple capabilities instead of acting only as a conversational chatbot.
The project focuses on the engineering challenges involved in connecting:
Reasoning
+
Memory
+
Voice
+
Vision
+
Automation
+
Task Planning
+
External Tools

into a single modular system.
Project Philosophy
JARVIS X is being developed around a few principles.
Modularity
Each major capability should remain independently extensible.
Reliability
Tasks should be observable, interruptible, and recoverable where possible.
Reproducibility
The project should become increasingly easier to install, test, and understand.
Responsible Automation
Computer-control capabilities should be designed with explicit user control and failure handling.
License
License information will be finalized after the dependency and third-party component audit.
Author
Aarav Pachouri
Student interested in Artificial Intelligence, Machine Learning, Software Engineering, and AI research.
GitHub: @aaravpachouri