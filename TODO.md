# TODO

## Config / Settings

- **Lazy settings initialization** — `settings = Settings()` in `src/marvin/config.py` runs at import time,
  meaning YAML/JSON loading, env interpolation, and pydantic validation all execute on first import. Consider
  a lazy singleton or factory pattern so imports stay cheap and tests can control initialization order without
  patching before import.
