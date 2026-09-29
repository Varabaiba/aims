# VAHA Project Instructions

AIMS Stands for AWTRIX Informer Middleware Server.
"AWTRIX NG" is a popular firwmare providing REST API services for informer displays.

AIMS Specifications are built on the following taxonomy:
Level 1: AIMS Components
AIMS.C1 is a FastAPI server running actual API operations and support activities
AIMS.C2 is a Streamlit multipage application that works with AIMS.C1 through its API

## Level 2: AIMS Functions
### AIMS.C1 Related functions - FastAPI App:
AIMS.C1.F1: Accepts AWTRIX NG "drop-in" compatible API calls and forwards them to actual AWTRIX NG host
AIMS.C1.F2: Accepts simple GET simplified GET requests, translates them and forwards them to actual AWTRIX NG host
AIMS.C1.F3: Accepts POST requests to schedule specific notifications based on CRON string
AIMS.C1.F4: Accepts DELETE requests to delete specific scheduled notifications
AIMS.C1.F5: Accepts GET requests to list all scheduled notifications
AIMS.C1.F6: Runs separate schedule thread to send scheduled notifications to actual AWTRIX NG host
AIMS.C1.F7: Manages all persistence needs through the sqlite database

### AIMS.C2 Related functions – Streamlit App:
AIMS.C2.F1: Provides a dedicated page to manage all configurations. Configurations are stored in the "settings.json" file in the project folder
AIMS.C2.F2: Provides a dedicated page to send notification via AIMS.C1.F1 function. The page shows all possible fields available for sending notifications populated with default values.
AIMS.C2.F3: Provides a dedicated page where it shows the configurable amount of log records for forwarding done via AIMS.C1.F1 & AIMS.C1.F2 functions
AIMS.C2.F3: Provides a dedicated page to manage schedules via AIMS.C1.F3 - F5 functions


## Instruction Scope

* Treat this file as the primary source of project-specific working rules.
* Before creating or modifying Python code, read and apply `.agents/PYTHON.md`.
* `.agents/PYTHON.md` defines mandatory Python naming, coding, documentation, testing, and source-structure conventions for this repository.
* Do not replace conventions defined in `.agents/PYTHON.md` with generic PEP recommendations where they differ.
* If a more specific `AGENTS.md` exists in a subdirectory, apply the more local file for work in that area.
* Explicit instructions from the user for the current task take precedence over repository guidance.
* Read Streamlit skills at `.venv\Lib\site-packages\streamlit\.agents\skills\developing-with-streamlit\SKILL.md`
* Read AWTRIX NG API Docs at `https://blueforcer.github.io/awtrix-ng/reference/http/`

## Project Principles

* Preserve the existing project architecture and established patterns unless the task requires changing them.
* Keep data collection, application logic, persistence, and Streamlit presentation responsibilities separated where the existing architecture provides such separation.
* Do not move application logic into Streamlit UI code merely for convenience.
* Reuse existing project services, helpers, models, and abstractions before introducing new ones.
* Prefer clear and maintainable implementations over unnecessarily complex solutions.
* Avoid introducing new dependencies when the Python standard library or an existing project dependency reasonably solves the problem.

