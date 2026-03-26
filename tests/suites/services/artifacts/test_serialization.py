from typing import cast

import pytest
from pydantic import ValidationError

from marvin.libs.config.artifacts import ArtifactFormat, ArtifactsConfig
from marvin.services.artifacts.schema.llm import LLMArtifactDataSchema, LLMArtifactSchema
from marvin.services.artifacts.serialization import (
    artifact_file_suffix,
    dumps_artifact,
    humanize_payload_for_yaml,
)


def test_humanize_payload_for_yaml_nested():
    payload = {"a": ["x\x00y", {"z": "\x1fb"}]}
    assert humanize_payload_for_yaml(payload) == {"a": ["xy", {"z": "b"}]}


def test_humanize_payload_for_yaml_expands_json_array_string():
    # A string that is a valid JSON array should be expanded into a list.
    payload = '[{"file": "a.py", "line": 1}]'
    result = humanize_payload_for_yaml(payload)
    assert result == [{"file": "a.py", "line": 1}]


def test_humanize_payload_for_yaml_expands_json_object_string():
    # A string that is a valid JSON object should be expanded into a dict.
    payload = '{"key": "value"}'
    result = humanize_payload_for_yaml(payload)
    assert result == {"key": "value"}


def test_humanize_payload_for_yaml_leaves_non_json_string_starting_with_bracket():
    # A string that starts and ends with [] but is not valid JSON must be left alone.
    payload = "[not valid json}"
    result = humanize_payload_for_yaml(payload)
    assert result == "[not valid json}"


def test_humanize_payload_for_yaml_does_not_expand_scalar_json():
    # Bare scalar JSON values (numbers, booleans, null) must not be expanded
    # to avoid unintended type coercion.
    assert humanize_payload_for_yaml("42") == "42"
    assert humanize_payload_for_yaml("true") == "true"
    assert humanize_payload_for_yaml("null") == "null"


def test_dumps_artifact_json_contains_fields():
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(prompt="p", response="r", prompt_system="s")
    )
    raw = dumps_artifact(artifact, ArtifactFormat.JSON)
    assert '"prompt": "p"' in raw


def test_artifacts_config_default_format_is_yaml():
    assert ArtifactsConfig().format is ArtifactFormat.YAML


def test_artifacts_config_rejects_invalid_format():
    with pytest.raises(ValidationError):
        ArtifactsConfig(format="toml")


def test_dumps_artifact_yaml_strips_controls_in_dump():
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(
            prompt="a\x00b",
            response="ok",
            prompt_system="sys",
        )
    )
    raw = dumps_artifact(artifact, ArtifactFormat.YAML)
    assert "ab" in raw
    assert "\x00" not in raw


def test_json_preserves_controls_with_escaping_while_yaml_sanitizes():
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(
            prompt="a\x00b",
            response="ok",
            prompt_system="sys",
        )
    )
    json_raw = dumps_artifact(artifact, ArtifactFormat.JSON)
    yaml_raw = dumps_artifact(artifact, ArtifactFormat.YAML)
    assert "\\u0000" in json_raw
    assert "\\x00" not in yaml_raw
    assert "ab" in yaml_raw


def test_dumps_artifact_yaml_multiline_uses_literal_block():
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(
            prompt="line1\nline2",
            response="x",
            prompt_system="sys",
        )
    )
    raw = dumps_artifact(artifact, ArtifactFormat.YAML)
    assert "prompt: |" in raw
    assert "line1" in raw
    assert "line2" in raw


def test_dumps_artifact_yaml_multiline_with_trailing_whitespace_uses_literal_block():
    # A line with trailing whitespace (common in diffs) must still produce block scalar
    # style. PyYAML falls back to double-quoted when trailing spaces are present, so
    # clean_multiline_string must strip them first.
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(
            prompt="line with trailing space   \nnext line",
            response="x",
            prompt_system="sys",
        )
    )
    raw = dumps_artifact(artifact, ArtifactFormat.YAML)
    assert "prompt: |" in raw


def test_dumps_artifact_yaml_expands_json_response():
    # The response field often contains a JSON array as a string. It should be
    # expanded into a YAML list structure, not emitted as a raw JSON string.
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(
            prompt="p",
            response='[{"file": "a.py", "line": 1, "message": "ok"}]',
            prompt_system="sys",
        )
    )
    raw = dumps_artifact(artifact, ArtifactFormat.YAML)
    # Should render as a YAML list, not a quoted JSON string.
    assert "- file: a.py" in raw
    assert "line: 1" in raw
    assert "message: ok" in raw


@pytest.mark.parametrize(
    ("fmt", "expected"),
    [
        (ArtifactFormat.JSON, ".json"),
        (ArtifactFormat.YAML, ".yaml"),
    ],
)
def test_artifact_file_suffix(fmt: ArtifactFormat, expected: str):
    assert artifact_file_suffix(fmt) == expected


def test_dumps_artifact_unsupported_format_raises():
    artifact = LLMArtifactSchema(
        data=LLMArtifactDataSchema(prompt="p", response="r", prompt_system="s")
    )
    with pytest.raises(ValueError, match="Unsupported artifact format"):
        dumps_artifact(artifact, cast("ArtifactFormat", "toml"))


def test_artifact_file_suffix_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported artifact format"):
        artifact_file_suffix(cast("ArtifactFormat", "toml"))
