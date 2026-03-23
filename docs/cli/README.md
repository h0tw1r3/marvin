# 📘 marvin CLI

The **marvin CLI** provides a simple interface to run reviews, inspect configuration, and integrate with CI/CD
pipelines.

It is built with Typer and fully supports async execution of all review modes.

---

## 🚀 Quick Start

After installing marvin:

````bash
pip install marvin
````

Run any command from your terminal:

```bash
marvin run
```

Or display help:

```bash
marvin --help
```

---

## 🧩 Available Commands

| Command                       | Description                                                               | Typical Usage                 |
|-------------------------------|---------------------------------------------------------------------------|-------------------------------|
| `marvin run`               | Runs the full review pipeline (inline + summary).                         | `marvin run`               |
| `marvin run-inline`        | Runs only **inline review** (line-by-line comments).                      | `marvin run-inline`        |
| `marvin run-context`       | Runs **context review** across multiple files for architectural feedback. | `marvin run-context`       |
| `marvin run-summary`       | Runs **summary review** that posts a single summarizing comment.          | `marvin run-summary`       |
| `marvin run-inline-reply`  | Generates **AI replies** to existing inline comment threads.              | `marvin run-inline-reply`  |
| `marvin run-summary-reply` | Generates **AI replies** to existing summary review threads.              | `marvin run-summary-reply` |
| `marvin clear-inline`      | Removes all **AI-generated inline comments** from the review.             | `marvin clear-inline`      |
| `marvin clear-summary`     | Removes all **AI-generated summary comments** from the review.            | `marvin clear-summary`     |
| `marvin show-config`       | Prints the currently resolved configuration (merged from YAML/JSON/ENV).  | `marvin show-config`       |

---

## 💡 Examples

### 🧠 Full Review

Runs the complete review cycle — inline + summary:

```bash
marvin run
```

### 🧩 Inline Review Only

For quick line-by-line comments:

```bash
marvin run-inline
```

Typical in CI/CD pipelines for fast feedback on changed files.

### 🧠 Context Review

For broader architectural or cross-file feedback:

```bash
marvin run-context
```

The model receives the entire diff set and can highlight inconsistencies between modules.

### 🗒️ Summary Review

Posts one concise summary comment under the merge/pull request:

```bash
marvin run-summary
```

Useful when inline feedback isn’t required but a global analysis is.

### 💬 Reply Modes

Generate AI-based follow-ups to existing discussion threads:

```bash
marvin run-inline-reply
marvin run-summary-reply
```

Replies only to comments originally created by marvin.

### 🧽 Clear Inline Comments

Removes all AI-generated inline comments:

```bash
marvin clear-inline
```

> ⚠️ **Warning**
>
> This command **permanently deletes** all inline review comments created by marvin in the current merge / pull
> request.
>
> - The operation cannot be undone
> - Only comments marked with the marvin inline tag are affected
> - Developer and user comments are not touched
>
> It is recommended to run this command **manually** and only when you are sure that existing AI comments are no longer
> needed.

### 🧽 Clear Summary Comments

Removes all AI-generated summary comments:

```bash
marvin clear-summary
```

> ⚠️ **Warning**
>
> This command **permanently deletes** all summary review comments created by marvin.
>
> - The operation cannot be undone
> - Only marvin summary comments are removed
> - No new comments are created as part of this command
>
> Use with caution, especially in shared or long-running pull requests.

### ⚙️ Inspect Configuration

Display the resolved configuration used by the CLI:

```bash
marvin show-config
```

Output (formatted JSON):

```json
{
  "llm": {
    "provider": "OPENAI",
    "meta": {
      "model": "gpt-4o-mini",
      "temperature": 0.3
    }
  },
  "vcs": {
    "provider": "GITLAB",
    "pipeline": {
      "project_id": 1
    }
  }
}
```

---

## ⚙️ Tips

- Each command runs **asynchronously** and handles exceptions internally.
- All reviews report **token usage** and **LLM cost** after completion.
- The CLI is designed for **non-interactive** use — perfect for CI/CD jobs.
