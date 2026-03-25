# TODO

## Architecture

- **langchain integration** — Refactor the codebase to leverage langchain's abstractions for agents
  to simplify implementation and improve maintainability.

## Features

- **Bedrock IRSA** - IRSA-enabled AWS Bedrock integration for LLM access without managing credentials, using boto3
  and IAM roles.

## Config / Settings

- **Lazy settings initialization** — `settings = Settings()` in `src/marvin/config.py` runs at import time,
  meaning YAML/JSON loading, env interpolation, and pydantic validation all execute on first import. Consider
  a lazy singleton or factory pattern so imports stay cheap and tests can control initialization order without
  patching before import.

## Documentation

- **Docstrings** — Add comprehensive docstrings to all public functions, classes, and modules using a consistent
  style (e.g., Google or NumPy) to improve code readability and maintainability. And enforce with a linter like
  `pydocstyle`.
- **Project README** - Expand the README with sections on features, usage, examples, and contribution guidelines.

## Logging

- **Structured logging** — Switch to structured logging (e.g., JSON) for better log parsing and integration with
  log management tools. This may involve using a library like `structlog` or configuring `loguru` to output JSON.

## Chores

- **Commit message linting** — Enforce a consistent commit message format (e.g., Conventional Commits) to improve
  readability and automate changelog generation.
