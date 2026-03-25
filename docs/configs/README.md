# 📘 marvin Configuration

marvin supports multiple configuration formats and sources. All of them are automatically detected at runtime.

---

## 📂 Supported formats

- **YAML** (recommended): `.marvin.yaml`
- **JSON**: `.marvin.json`
- **ENV**: `.env`

👉 You can combine formats: values are loaded in order of priority.

---

## 📑 Load priority

1. **YAML** (`.marvin.yaml` or path from `MARVIN_CONFIG_FILE_YAML`)
2. **JSON** (`.marvin.json` or path from `MARVIN_CONFIG_FILE_JSON`)
3. **ENV** (`.env` or path from `MARVIN_CONFIG_FILE_ENV`)
4. **Environment variables** (`LLM__PROVIDER=OPENAI`, etc.)
5. **Initialization arguments** (if used as a library)

---

## ⚙️ Override file paths

You can override default config locations using environment variables:

- `MARVIN_CONFIG_FILE_YAML` — path to `.yaml` config
- `MARVIN_CONFIG_FILE_JSON` — path to `.json` config
- `MARVIN_CONFIG_FILE_ENV` — path to `.env`

By default, configs are loaded from the **project root**.

## Artifacts serialization

When configuring artifacts:

- `ARTIFACTS__FORMAT=yaml` (default): human-readable debug output; sanitizes control characters and is not byte-faithful
- `ARTIFACTS__FORMAT=json`: exact/lossless output for machine parsing and archival fidelity

---

## 📘 Examples

- [.marvin.yaml](./.marvin.yaml) — main YAML config with comments
- [.marvin.json](./.marvin.json) — JSON config example
- [.env.example](./.env.example) — ENV config example

---

## Environment variable interpolation

YAML and JSON config files support **Docker Compose–style** variable interpolation.
Any string **value** (not keys) can reference process environment variables using `$VAR` or `${VAR}` syntax.
See the [Docker Compose interpolation reference](https://docs.docker.com/reference/compose-file/interpolation/) for the full grammar.

### Supported forms

| Syntax | Meaning |
|---|---|
| `$VAR` / `${VAR}` | Value of `VAR`, or empty + warning if unset |
| `${VAR:-default}` | Value of `VAR` if set and non-empty, else `default` |
| `${VAR-default}` | Value of `VAR` if set (even empty), else `default` |
| `${VAR:?error}` | Value of `VAR` if set and non-empty, else **fail** with `error` |
| `${VAR?error}` | Value of `VAR` if set, else **fail** with `error` |
| `${VAR:+replacement}` | `replacement` if `VAR` set and non-empty, else empty |
| `${VAR+replacement}` | `replacement` if `VAR` set (even empty), else empty |
| `$$` | Literal `$` (escape) |

Nested expressions are supported: `${VAR:-${FALLBACK:-last_resort}}`.

### Example `.marvin.yaml`

```yaml
llm:
  provider: OPENAI
  meta:
    model: ${MARVIN_MODEL:-gpt-4o}
  http_client:
    api_token: ${OPENAI_API_KEY:?OPENAI_API_KEY must be set}
```

### Important notes

- **Lookup source**: interpolation reads from the **process environment**
  (`os.environ`) only. The `.env` file is a separate loading mechanism and is
  _not_ used as a source for interpolation.
- **Empty results treated as unset**: if interpolation resolves a config value
  to an empty string, the key is treated as unset — allowing pydantic-settings
  to fall through to defaults or lower-priority sources. This is an intentional
  difference from Docker Compose.
- **Literal empty strings are preserved**: a value of `""` written directly in
  the config file (without interpolation tokens) remains an explicit empty
  string.
- **Malformed patterns are preserved**: unmatched `${`, `${}`, or `$` followed
  by a non-name character are kept as literal text.

---

## 🔍 Tips

- Use **YAML** for most projects — it’s human-friendly and supports comments.
- **JSON** is convenient for automation (e.g., CI/CD pipelines).
- **ENV** is useful for local development and quick overrides.
