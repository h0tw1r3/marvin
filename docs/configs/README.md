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

---

## 📘 Examples

- [.marvin.yaml](./.marvin.yaml) — main YAML config with comments
- [.marvin.json](./.marvin.json) — JSON config example
- [.env.example](./.env.example) — ENV config example

---

## 🔍 Tips

- Use **YAML** for most projects — it’s human-friendly and supports comments.
- **JSON** is convenient for automation (e.g., CI/CD pipelines).
- **ENV** is useful for local development and quick overrides.
