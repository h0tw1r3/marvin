"""Serialize artifact models to JSON or human-oriented YAML."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

import yaml

from marvin.libs.config.artifacts import ArtifactFormat

if TYPE_CHECKING:
    from marvin.services.artifacts.schema.base import BaseArtifactSchema


def _strip_control_chars(text: str) -> str:
    """Remove C0/C1 control characters that make YAML hard to read or unsafe.

    Preserves tab, LF, and CR. Strips other ASCII controls, DEL, and Unicode C1 controls
    (U+0080–U+009F). This intentionally mutates content for display-oriented YAML only.
    """
    allowed = "\t\n\r"
    out: list[str] = []
    for ch in text:
        o = ord(ch)
        if ch in allowed:
            out.append(ch)
            continue
        if o < 32 or o == 127 or 0x80 <= o <= 0x9F:
            continue
        out.append(ch)
    return "".join(out)


def clean_multiline_string(text: str) -> str:
    """Normalize string content before YAML literal block output.

    Strips control characters and trailing whitespace from each line. Trailing
    whitespace on a line prevents PyYAML from choosing literal block style (``|``)
    because block scalars would silently discard those spaces. Since YAML artifacts
    are display-oriented (explicitly lossy), stripping trailing spaces is acceptable.
    """
    cleaned = _strip_control_chars(text)
    lines = [line.rstrip() for line in cleaned.splitlines()]
    result = "\n".join(lines)
    # Preserve a trailing newline if the original had one.
    if cleaned.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


class ArtifactYamlDumper(yaml.SafeDumper):
    """SafeDumper with readable multiline strings (literal block ``|``)."""


def _represent_str_for_artifact_yaml(dumper: yaml.Dumper, data: str) -> yaml.nodes.ScalarNode:
    """Use literal block style for multiline strings so prompts/responses stay readable.

    This cleanup is a defensive backstop for multiline emission. The primary cleanup path
    is ``humanize_payload_for_yaml`` which sanitizes all strings recursively.
    """
    if "\n" in data:
        cleaned = clean_multiline_string(data)
        return dumper.represent_scalar("tag:yaml.org,2002:str", cleaned, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


ArtifactYamlDumper.add_representer(str, _represent_str_for_artifact_yaml)


def humanize_payload_for_yaml(value: Any) -> Any:
    """Recursively sanitize all strings in JSON-like payloads for readable YAML dumps.

    Strings that look like JSON objects or arrays (delimited by ``{}``) or ``[]``)
    are parsed and expanded into native Python structures so they render as proper
    YAML instead of opaque single-line strings. Only object/array JSON is expanded;
    bare scalar JSON (numbers, booleans, null) is left as-is to avoid unintended
    type coercion.
    """
    if isinstance(value, str):
        stripped = value.strip()
        if (
            (stripped.startswith("{") and stripped.endswith("}"))
            or (stripped.startswith("[") and stripped.endswith("]"))
        ):
            try:
                parsed = json.loads(value)
                # Recurse so any nested JSON strings are also expanded.
                return humanize_payload_for_yaml(parsed)
            except (json.JSONDecodeError, ValueError):
                pass
        return _strip_control_chars(value)
    if isinstance(value, dict):
        return {k: humanize_payload_for_yaml(v) for k, v in value.items()}
    if isinstance(value, list):
        return [humanize_payload_for_yaml(item) for item in value]
    return value


def dumps_artifact(artifact: BaseArtifactSchema, fmt: ArtifactFormat) -> str:
    """Serialize ``artifact`` to a UTF-8 text blob (JSON or YAML)."""
    if fmt is ArtifactFormat.JSON:
        return artifact.model_dump_json(indent=2)

    if fmt is ArtifactFormat.YAML:
        payload = artifact.model_dump(mode="json")
        # Primary sanitization pass: apply readability cleanup to every string field.
        payload = humanize_payload_for_yaml(payload)
        # Use yaml.dump (not safe_dump): safe_dump hard-codes Dumper=SafeDumper and would
        # conflict with Dumper=ArtifactYamlDumper. Subclass extends SafeDumper — still safe.
        # width=sys.maxsize intentionally avoids line wrapping for long prompt/response lines.
        return yaml.dump(
            payload,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=sys.maxsize,
            Dumper=ArtifactYamlDumper,
        )

    raise ValueError(f"Unsupported artifact format: {fmt!r}")


def artifact_file_suffix(fmt: ArtifactFormat) -> str:
    if fmt is ArtifactFormat.JSON:
        return ".json"
    if fmt is ArtifactFormat.YAML:
        return ".yaml"
    raise ValueError(f"Unsupported artifact format: {fmt!r}")
