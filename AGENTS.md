# VAHA Project Instructions

AIMS Stands for AWTRIX Informer Middleware Server.
AIMS is a Streamlit-based modern multipage app.
Each page serves its own function.
AIMS Server accepts API inputs though POST method
AIMS Server accepts UI inputs through Streamlit UI
AIMS Server forwards both API and UI inputs to the configured AWTRIX server 


## Instruction Scope

* Treat this file as the primary source of project-specific working rules.
* Before creating or modifying Python code, read and apply `.agents/PYTHON.md`.
* `.agents/PYTHON.md` defines mandatory Python naming, coding, documentation, testing, and source-structure conventions for this repository.
* Do not replace conventions defined in `.agents/PYTHON.md` with generic PEP recommendations where they differ.
* If a more specific `AGENTS.md` exists in a subdirectory, apply the more local file for work in that area.
* Explicit instructions from the user for the current task take precedence over repository guidance.
* Read Streamlit skills at `.venv\Lib\site-packages\streamlit\.agents\skills\developing-with-streamlit\SKILL.md`

## Project Principles

* Preserve the existing project architecture and established patterns unless the task requires changing them.
* Keep data collection, application logic, persistence, and Streamlit presentation responsibilities separated where the existing architecture provides such separation.
* Do not move application logic into Streamlit UI code merely for convenience.
* Reuse existing project services, helpers, models, and abstractions before introducing new ones.
* Prefer clear and maintainable implementations over unnecessarily complex solutions.
* Avoid introducing new dependencies when the Python standard library or an existing project dependency reasonably solves the problem.

