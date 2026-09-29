# Python Development Conventions

This file defines the Python coding conventions used by this repository.

These conventions are intentional project requirements. Where they differ from generic PEP recommendations, the conventions defined here take precedence.

## Naming Conventions

Use lowercase `snake_case` names except for classes and types.

### Variables

Prefix variables with `x_`.

```python
x_name = "example"
x_result = []
x_file_path = None
```

Use meaningful names after the prefix.

Prefer:

```python
x_customer_name
x_response_data
x_output_path
```

over:

```python
x_a
x_tmp
x_val
```

unless the shorter name has an obvious and highly localized meaning.

### Function and Method Parameters

Prefix function and method parameters with `a_`.

```python
def build_url(a_base_url: str, a_path: str) -> str:
    ...
```

The `self` and `cls` parameters are exempt from this rule.

### Constants

Prefix constants with `c_` and keep them lowercase.

```python
c_max_retries = 3
c_default_timeout = 30
```

Do not convert project constants to conventional uppercase naming merely to conform to PEP 8.

### Functions and Methods

Use lowercase `snake_case`.

```python
def build_request():
    ...
```

### Classes and Types

Use `PascalCase`.

```python
class YoutubeClient:
    ...
```

## Imports

Separate imports into the following groups using the indicated comments:

```python
# INT
from pathlib import Path
import json

# EXT
import requests
import streamlit as st

# OWN
from ytrs.models import VideoInfo
from ytrs.youtube import YoutubeClient
```

Use:

* `# INT` for Python standard-library modules.
* `# EXT` for third-party/external libraries.
* `# OWN` for project-owned modules.

Keep imports grouped consistently.

Avoid wildcard imports.

Prefer importing from the project's intended public module interface rather than reaching unnecessarily into implementation internals.

Remove unused imports when modifying a file.

## Type Annotations

Use type annotations for function and method parameters and return values.

```python
def load_video(a_video_id: str) -> VideoInfo | None:
    ...
```

Annotate important data structures where the type is not immediately obvious.

Prefer precise types over `Any`.

Use `Any` only when the underlying value is genuinely unconstrained or when interacting with an external interface that cannot reasonably be typed more precisely.

Do not introduce complex typing constructs where they make otherwise straightforward code harder to understand.

## Functions and Methods

Keep functions focused on a clear responsibility.

Prefer smaller, composable functions over large functions containing unrelated responsibilities.

Avoid hidden mutation of unrelated state.

Return results explicitly rather than relying on obscure side effects.

Do not use mutable objects as default parameter values.

Prefer readable control flow over compressed or clever implementations.

## Main Block

Every project-owned Python unit should include the following block at the end of the module:

```python
if __name__ == "__main__":
    pass
```

This block is intentionally present to provide a convenient location for immediate manual testing and diagnostic code during development.

When manual testing is required, place the temporary execution code directly inside this block.

Example:

```python
if __name__ == "__main__":
    x_value = "example"
    x_result = process_value(x_value)

    print(x_result)
```

Follow these rules:

* Keep the block at the end of the module.
* Code inside the block must execute only when the module is run directly.
* Importing the module must not trigger manual-test behavior.
* Do not create a separate `main()` function solely to satisfy this convention.
* Create a `main()` function only when it is genuinely useful to the module or application design.
* Keep manual test and diagnostic code lightweight and understandable.
* Do not use the block as a substitute for automated tests.
* Do not perform irreversible operations merely for manual testing.
* Do not modify production data merely for testing.
* Do not embed credentials, API keys, tokens, passwords, or other secrets.
* Avoid expensive external API calls unless they are explicitly required for the intended manual test.
* When no manual test code is required, retain the block with `pass`.

## Documentation

Add docstrings to all project-owned functions and methods.

Docstrings should explain the purpose of the function or method and, where useful:

* important parameters;
* returned values;
* relevant side effects;
* raised exceptions;
* non-obvious constraints.

Avoid docstrings that merely repeat the function name in prose.

Prefer:

```python
def load_config(a_path: Path) -> dict[str, object]:
    """Load and parse application configuration from a JSON file."""
```

over:

```python
def load_config(a_path: Path) -> dict[str, object]:
    """Load config."""
```

Keep docstrings concise when the function's behavior is simple.

## Comments

Use comments generously enough to make the logical structure of non-trivial code easy to follow.

Add comments for meaningful logical stages inside functions and methods.

For example:

```python
# Build the request parameters from the current application state.
x_params = ...

# Request the next page from YouTube.
x_response = ...

# Normalize the external response into internal data structures.
x_items = ...
```

Comments should primarily explain:

* intent;
* logical stages;
* constraints;
* assumptions;
* non-obvious decisions;
* reasons for unusual implementation choices.

Do not add comments that merely translate an obvious Python statement into English.

Avoid:

```python
# Increase counter by one.
x_counter += 1
```

unless the reason for increasing the counter is itself non-obvious.

Add comments inside the `if __name__ == "__main__":` block when the manual test or diagnostic setup is not self-explanatory.

## Readability

Prefer readable and explicit code over clever or unnecessarily compact solutions.

Optimize for somebody understanding the code later rather than minimizing line count.

Prefer straightforward control flow.

Avoid deeply nested expressions where intermediate variables make the logic clearer.

Use early returns when they simplify control flow.

Do not introduce abstractions solely to eliminate a very small amount of duplication.

Prefer existing project patterns over introducing a new style for equivalent functionality.

## Paths and Files

Prefer `pathlib.Path` for new filesystem code.

```python
from pathlib import Path
```

Use context managers when opening files and other resources.

Specify text encoding explicitly.

```python
with x_path.open("r", encoding="utf-8") as x_file:
    x_text = x_file.read()
```

Do not rely on the operating system's default text encoding.

Assume that the application may run on Windows.

Avoid hard-coded path separators.

Prefer path composition:

```python
x_path = x_base_path / "data" / "output.json"
```

over manual string construction:

```python
x_path = x_base_path + "\\data\\output.json"
```

## Exceptions

Catch specific exceptions rather than using bare `except:` blocks.

Avoid:

```python
try:
    ...
except:
    ...
```

Prefer:

```python
try:
    ...
except ValueError as x_exception:
    ...
```

Do not silently suppress exceptions without a clear reason.

Preserve useful exception context when wrapping exceptions.

Use exceptions for exceptional conditions rather than routine branching where a normal return value is clearer.

Avoid catching `Exception` broadly unless the application boundary genuinely requires it.

## Resource Management

Use context managers for files, database connections, temporary resources, and other objects that require deterministic cleanup when supported by the relevant API.

Avoid leaving external resources open beyond the scope where they are required.

Explicitly close resources when the API does not support a context manager.

## Logging

Use the project's existing logging approach.

Do not introduce a second logging framework without a project-level reason.

Log information that is useful for diagnosing application behavior.

Do not log:

* passwords;
* API keys;
* access tokens;
* refresh tokens;
* client secrets;
* authentication headers;
* other sensitive credentials.

Avoid excessive logging inside tight loops unless diagnostic detail is explicitly required.

Use appropriate log levels rather than treating every event as informational or erroneous.

## External Data

Treat external API and file data as potentially incomplete or malformed.

Validate assumptions about:

* missing fields;
* `None` values;
* unexpected types;
* empty collections;
* malformed values;
* pagination;
* unexpected responses.

Do not assume an external API always returns every optional field.

Keep transformations from external representation to internal representation explicit where practical.

Preserve raw external identifiers unless application logic explicitly requires their transformation.

## Collections and Iteration

Prefer direct iteration over unnecessary index-based loops.

Prefer:

```python
for x_item in x_items:
    ...
```

over:

```python
for x_index in range(len(x_items)):
    x_item = x_items[x_index]
```

unless the index itself is required.

Use comprehensions when they remain immediately readable.

Use ordinary loops when filtering, transformation, error handling, or comments make a comprehension harder to understand.

Avoid modifying a collection while iterating over it unless the behavior is intentional and safe.

## Data Structures

Prefer appropriate standard-library structures before introducing custom containers.

Use `dataclass` where a lightweight typed data object is appropriate.

Use frozen dataclasses where immutability is intentional and useful.

Use enums when a value is restricted to a stable and meaningful predefined set.

Do not rely on object hash behavior without considering all fields participating in equality and hashing.

Prefer explicit data structures over loosely structured dictionaries when the data has a stable internal schema.

## Dependencies

Prefer solutions in this order:

1. Python standard library.
2. Dependencies already used by the project.
3. A new external dependency when it provides a clear practical benefit.

Do not add a dependency for functionality that can be implemented clearly and reliably with existing project tools.

Do not replace an established project dependency merely because another library offers equivalent functionality.

When adding a dependency is necessary, keep its usage localized where practical.

## Testing

Use the project's established testing framework and test structure.

Tests should primarily verify observable behavior rather than mirror internal implementation.

Prefer focused tests covering one behavioral concern.

Keep tests deterministic.

Tests should not depend on execution order.

Avoid real network calls in unit tests unless the test is explicitly intended as an integration test.

Use fixtures and reusable helpers where they improve clarity and avoid repeated setup.

When fixing a bug, add or update a regression test where practical.

Manual testing through the module's `if __name__ == "__main__":` block complements automated testing but does not replace it.

## Changes to Existing Code

When modifying existing Python code:

* Preserve the established architecture.
* Preserve existing public behavior unless the task requires changing it.
* Follow the naming conventions in this document for newly created identifiers.
* Preserve existing project naming conventions when extending nearby code.
* Do not rename existing identifiers solely to normalize them to generic Python style.
* Keep unrelated formatting or restructuring out of focused changes.
* Remove dead code introduced by the change.
* Update affected docstrings and comments when behavior changes.
* Avoid introducing a second implementation of functionality already provided elsewhere in the project.
* Reuse existing helpers and abstractions where appropriate.

## Final Quality Check

Before completing Python code changes, check that:

* variables use the `x_` prefix;
* function and method parameters use the `a_` prefix;
* constants use the `c_` prefix;
* classes and types use `PascalCase`;
* import groups use `# INT`, `# EXT`, and `# OWN`;
* functions and methods have useful docstrings;
* meaningful logical stages are commented where appropriate;
* comments do not merely restate obvious Python statements;
* type annotations are present where required;
* filesystem code uses portable paths;
* text files use explicit encoding;
* exceptions are handled specifically;
* external resources are managed safely;
* secrets are not present in code or logs;
* the module contains the standard `if __name__ == "__main__":` block;
* relevant tests or checks have been run where practical.
