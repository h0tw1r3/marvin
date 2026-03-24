"""Tests for Docker Compose–style config interpolation.

Organised in three layers:
  1. ``interpolate_compose`` — string-level unit tests
  2. ``expand_env_in_structure`` — structure walk / omission tests
  3. Integration — end-to-end via the settings source classes
"""

import logging

import pytest

from marvin.libs.config.interpolation import (
    InterpolationError,
    _apply_modifier,
    _warn_unresolved,
    expand_env_in_structure,
    interpolate_compose,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _propagate_loguru(caplog):
    """Route loguru into stdlib logging so ``caplog`` captures warnings."""
    from loguru import logger

    class _Sink:
        def write(self, message):
            record = message.record
            level = record["level"].no
            py_level = {
                10: logging.DEBUG,
                20: logging.INFO,
                30: logging.WARNING,
                40: logging.ERROR,
                50: logging.CRITICAL,
            }.get(level, logging.INFO)
            logging.getLogger("loguru").log(py_level, str(message).rstrip())

    handler_id = logger.add(_Sink(), format="{message}", level="WARNING")
    with caplog.at_level(logging.WARNING, logger="loguru"):
        yield
    logger.remove(handler_id)


def _env(*pairs: tuple[str, str]) -> dict[str, str]:
    """Build a minimal env mapping from key-value pairs."""
    return dict(pairs)


# ===================================================================
# Layer 1: interpolate_compose — string-level
# ===================================================================


class TestInterpolateComposeDirect:
    """Direct ``$VAR`` and ``${VAR}`` substitution."""

    def test_unbraced(self):
        assert interpolate_compose("$FOO", env=_env(("FOO", "bar"))) == "bar"

    def test_braced(self):
        assert interpolate_compose("${FOO}", env=_env(("FOO", "bar"))) == "bar"

    def test_embedded(self):
        assert interpolate_compose("a-${X}-b", env=_env(("X", "y"))) == "a-y-b"

    def test_multiple(self):
        env = _env(("A", "1"), ("B", "2"))
        assert interpolate_compose("$A and ${B}", env=env) == "1 and 2"

    def test_unresolved_returns_empty(self):
        assert interpolate_compose("${NOPE}", env={}) == ""

    def test_no_tokens_passthrough(self):
        assert interpolate_compose("plain text", env={}) == "plain text"

    def test_empty_string_passthrough(self):
        assert interpolate_compose("", env={}) == ""


class TestInterpolateComposeEscapeAndLiteral:
    """``$$`` escape and literal ``$`` edge cases."""

    def test_double_dollar(self):
        assert interpolate_compose("$$HOME", env={}) == "$HOME"

    def test_double_dollar_mid_string(self):
        assert interpolate_compose("a$$b", env={}) == "a$b"

    def test_lone_dollar_at_end(self):
        assert interpolate_compose("end$", env={}) == "end$"

    def test_dollar_before_digit(self):
        assert interpolate_compose("$123", env={}) == "$123"

    def test_dollar_before_space(self):
        assert interpolate_compose("$ space", env={}) == "$ space"


class TestInterpolateComposeModifiers:
    """Braced modifier forms: ``:-``, ``-``, ``:+``, ``+``, ``:?``, ``?``."""

    # -- default (:-) --
    def test_default_colon_dash_unset(self):
        assert interpolate_compose("${X:-fallback}", env={}) == "fallback"

    def test_default_colon_dash_empty(self):
        assert interpolate_compose("${X:-fallback}", env=_env(("X", ""))) == "fallback"

    def test_default_colon_dash_set(self):
        assert interpolate_compose("${X:-fallback}", env=_env(("X", "val"))) == "val"

    # -- default (-) --
    def test_default_dash_unset(self):
        assert interpolate_compose("${X-fallback}", env={}) == "fallback"

    def test_default_dash_empty_counts_as_set(self):
        assert interpolate_compose("${X-fallback}", env=_env(("X", ""))) == ""

    def test_default_dash_set(self):
        assert interpolate_compose("${X-fallback}", env=_env(("X", "val"))) == "val"

    # -- replacement (:+) --
    def test_replacement_colon_plus_set(self):
        assert interpolate_compose("${X:+yes}", env=_env(("X", "val"))) == "yes"

    def test_replacement_colon_plus_empty(self):
        assert interpolate_compose("${X:+yes}", env=_env(("X", ""))) == ""

    def test_replacement_colon_plus_unset(self):
        assert interpolate_compose("${X:+yes}", env={}) == ""

    # -- replacement (+) --
    def test_replacement_plus_set(self):
        assert interpolate_compose("${X+yes}", env=_env(("X", "val"))) == "yes"

    def test_replacement_plus_empty(self):
        assert interpolate_compose("${X+yes}", env=_env(("X", ""))) == "yes"

    def test_replacement_plus_unset(self):
        assert interpolate_compose("${X+yes}", env={}) == ""

    # -- required (:?) --
    def test_required_colon_question_set(self):
        assert interpolate_compose("${X:?oops}", env=_env(("X", "val"))) == "val"

    def test_required_colon_question_empty_raises(self):
        with pytest.raises(InterpolationError, match="oops"):
            interpolate_compose("${X:?oops}", env=_env(("X", "")))

    def test_required_colon_question_unset_raises(self):
        with pytest.raises(InterpolationError, match="oops"):
            interpolate_compose("${X:?oops}", env={})

    # -- required (?) --
    def test_required_question_set(self):
        assert interpolate_compose("${X?oops}", env=_env(("X", "val"))) == "val"

    def test_required_question_empty_ok(self):
        assert interpolate_compose("${X?oops}", env=_env(("X", ""))) == ""

    def test_required_question_unset_raises(self):
        with pytest.raises(InterpolationError, match="oops"):
            interpolate_compose("${X?oops}", env={})

    def test_required_whitespace_only_operand_falls_back_to_name(self):
        """Whitespace-only error text should fall back to variable name."""
        with pytest.raises(InterpolationError, match="X"):
            interpolate_compose("${X:? }", env={})

    def test_required_empty_operand_falls_back_to_name(self):
        with pytest.raises(InterpolationError, match="X"):
            interpolate_compose("${X:?}", env={})


class TestInterpolateComposeNesting:
    """Nested ``${…}`` inside modifier operands."""

    def test_nested_default(self):
        env = _env(("INNER", "deep"))
        assert interpolate_compose("${OUTER:-${INNER}}", env=env) == "deep"

    def test_double_nested_default(self):
        assert (
            interpolate_compose("${A:-${B:-last}}", env={}) == "last"
        )

    def test_nested_with_set_outer(self):
        env = _env(("OUTER", "top"))
        assert interpolate_compose("${OUTER:-${INNER:-x}}", env=env) == "top"


class TestInterpolateComposeMalformed:
    """Malformed patterns preserved as literals."""

    def test_unmatched_brace(self):
        assert interpolate_compose("${VAR", env={}) == "${VAR"

    def test_empty_braces(self):
        assert interpolate_compose("${}", env={}) == "${}"

    def test_invalid_name_in_braces(self):
        assert interpolate_compose("${123}", env={}) == "${123}"

    def test_dollar_digit_unbraced(self):
        assert interpolate_compose("$1abc", env={}) == "$1abc"

    def test_truncated_colon_modifier(self):
        """``${VAR:`` at end of string — colon but no modifier char."""
        assert interpolate_compose("${VAR:", env={}) == "${VAR:"

    def test_unclosed_modifier_operand(self):
        """``${VAR:-default`` without closing brace."""
        assert interpolate_compose("${VAR:-default", env={}) == "${VAR:-default"

    def test_unknown_char_after_name(self):
        """``${VAR=val}`` — ``=`` is not a valid modifier."""
        assert interpolate_compose("${VAR=val}", env={}) == "${VAR=val}"

    def test_unknown_char_after_colon(self):
        """``${VAR:=val}`` — ``:=`` is not a valid modifier."""
        assert interpolate_compose("${VAR:=val}", env={}) == "${VAR:=val}"


class TestInterpolateComposeUnbracedResolve:
    """Unbraced ``$VAR`` resolution through ``_resolve_dollar``."""

    def test_unbraced_unresolved_returns_empty(self):
        assert interpolate_compose("hello-$MISSING-world", env={}) == "hello--world"

    def test_unbraced_unresolved_in_operand(self):
        """Unbraced ``$VAR`` inside a modifier operand resolves via ``_resolve_dollar``."""
        assert interpolate_compose("${X:-$FALLBACK}", env=_env(("FALLBACK", "fb"))) == "fb"

    def test_env_defaults_to_os_environ(self, monkeypatch):
        """Calling ``interpolate_compose`` without ``env`` reads ``os.environ``."""
        monkeypatch.setenv("_IC_TEST_OSENV", "from_os")
        assert interpolate_compose("$_IC_TEST_OSENV") == "from_os"


class TestInterpolateComposeMixedStrings:
    """Mixed literal + interpolation in one string."""

    def test_prefix_suffix_missing(self):
        assert interpolate_compose("prefix-${MISSING}-suffix", env={}) == "prefix--suffix"

    def test_prefix_suffix_present(self):
        env = _env(("X", "val"))
        assert interpolate_compose("prefix-${X}-suffix", env=env) == "prefix-val-suffix"


# ===================================================================
# Layer 2: expand_env_in_structure — structure walk
# ===================================================================


class TestExpandEnvDict:
    """Dict-level expansion: omission, preservation, non-pruning."""

    def test_simple_expansion(self):
        obj = {"key": "${A}"}
        assert expand_env_in_structure(obj, env=_env(("A", "val"))) == {"key": "val"}

    def test_interpolated_empty_omits_key(self):
        obj = {"present": "ok", "gone": "${MISSING}"}
        result = expand_env_in_structure(obj, env={})
        assert result == {"present": "ok"}
        assert "gone" not in result

    def test_literal_empty_string_preserved(self):
        obj = {"empty": ""}
        assert expand_env_in_structure(obj, env={}) == {"empty": ""}

    def test_nested_dict_child_omitted_parent_kept(self):
        obj = {"parent": {"keep": "yes", "drop": "${MISSING}"}}
        result = expand_env_in_structure(obj, env={})
        assert result == {"parent": {"keep": "yes"}}
        assert "parent" in result

    def test_non_string_values_unchanged(self):
        obj = {"num": 42, "flag": True, "nothing": None, "pi": 3.14}
        assert expand_env_in_structure(obj, env={}) == obj

    def test_mixed_string_not_omitted(self):
        obj = {"mixed": "a-${MISSING}-b"}
        result = expand_env_in_structure(obj, env={})
        assert result == {"mixed": "a--b"}


class TestExpandEnvList:
    """List-level expansion: items preserved as ``""``."""

    def test_list_items_expanded(self):
        obj = {"items": ["${A}", "${B}"]}
        env = _env(("A", "x"), ("B", "y"))
        assert expand_env_in_structure(obj, env=env) == {"items": ["x", "y"]}

    def test_list_item_empty_preserved(self):
        obj = {"items": ["keep", "${MISSING}", "also"]}
        result = expand_env_in_structure(obj, env={})
        assert result == {"items": ["keep", "", "also"]}
        assert len(result["items"]) == 3

    def test_list_of_dicts(self):
        obj = {"items": [{"a": "${X}"}, {"b": "${MISSING}"}]}
        env = _env(("X", "found"))
        result = expand_env_in_structure(obj, env=env)
        assert result == {"items": [{"a": "found"}, {}]}


class TestApplyModifierGuard:
    """Verify _apply_modifier raises on unknown modifiers (R3 fix)."""

    def test_unknown_modifier_raises_assertion(self):
        with pytest.raises(AssertionError, match="Unknown modifier: '!'"):
            _apply_modifier("X", "!", colon=False, operand="", env={})

    def test_unknown_modifier_with_colon_raises_assertion(self):
        with pytest.raises(AssertionError, match="Unknown modifier: '@'"):
            _apply_modifier("X", "@", colon=True, operand="default", env={"X": "val"})


class TestWarnUnresolved:
    """Verify _warn_unresolved deduplication (R1 fix)."""

    def test_warns_first_occurrence(self, caplog):
        warned: set[str] = set()
        _warn_unresolved("MY_VAR", warned)
        assert "MY_VAR" in warned
        assert any("MY_VAR" in r.message for r in caplog.records)

    def test_second_call_suppressed(self, caplog):
        warned: set[str] = set()
        _warn_unresolved("MY_VAR", warned)
        caplog.clear()
        _warn_unresolved("MY_VAR", warned)
        assert not any("MY_VAR" in r.message for r in caplog.records)


class TestExpandEnvWarnings:
    """Warning deduplication and suppression."""

    def test_unresolved_warns_once(self, caplog):
        obj = {"a": "${MISSING}", "b": "${MISSING}", "c": "${MISSING}"}
        expand_env_in_structure(obj, env={})
        warning_msgs = [r.message for r in caplog.records if "MISSING" in r.message]
        assert len(warning_msgs) == 1

    def test_nested_default_resolved_no_warning(self, caplog):
        obj = {"val": "${OUTER:-${MISSING:-fallback}}"}
        result = expand_env_in_structure(obj, env={})
        assert result == {"val": "fallback"}
        warning_msgs = [r.message for r in caplog.records if "MISSING" in r.message]
        assert len(warning_msgs) == 0

    def test_required_modifier_raises_not_warns(self, caplog):
        obj = {"val": "${REQUIRED:?must set this}"}
        with pytest.raises(InterpolationError, match="must set this"):
            expand_env_in_structure(obj, env={})


class TestExpandEnvEdgeCases:
    """Tuples, empty dicts, deeply nested structures, env isolation."""

    def test_tuple_returned_unchanged(self):
        result = expand_env_in_structure(("a", "b"), env={})
        assert result == ("a", "b")

    def test_empty_dict(self):
        assert expand_env_in_structure({}, env={}) == {}

    def test_deeply_nested(self):
        obj = {"l1": {"l2": {"l3": "${DEEP}"}}}
        env = _env(("DEEP", "found"))
        assert expand_env_in_structure(obj, env=env) == {"l1": {"l2": {"l3": "found"}}}

    def test_empty_env_is_truly_empty(self, monkeypatch):
        """Passing ``env={}`` must not fall through to ``os.environ``."""
        monkeypatch.setenv("_INTERP_TEST_VAR", "from_os")
        obj = {"val": "${_INTERP_TEST_VAR}"}
        result = expand_env_in_structure(obj, env={})
        assert "val" not in result

    def test_none_env_uses_os_environ(self, monkeypatch):
        monkeypatch.setenv("_INTERP_TEST_VAR", "from_os")
        obj = {"val": "${_INTERP_TEST_VAR}"}
        result = expand_env_in_structure(obj, env=None)
        assert result == {"val": "from_os"}


# ===================================================================
# Layer 3: Integration — settings source classes
# ===================================================================


class TestInterpolatingYamlSettingsSource:
    """End-to-end via InterpolatingYamlSettingsSource."""

    def test_interpolated_yaml_loads(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / ".marvin.yaml"
        yaml_file.write_text(
            "core:\n  provider_name: ${_TEST_PROVIDER:-default_provider}\n"
        )
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))
        monkeypatch.setenv("_TEST_PROVIDER", "my_provider")

        from marvin.config import InterpolatingYamlSettingsSource
        from pydantic_settings import BaseSettings, InitSettingsSource

        source = InterpolatingYamlSettingsSource(BaseSettings)
        assert isinstance(source, InitSettingsSource)
        assert source.init_kwargs.get("core", {}).get("provider_name") == "my_provider"

    def test_missing_yaml_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(tmp_path / "nonexistent.yaml"))

        from marvin.config import InterpolatingYamlSettingsSource
        from pydantic_settings import BaseSettings

        source = InterpolatingYamlSettingsSource(BaseSettings)
        assert source.init_kwargs == {}

    def test_invalid_yaml_raises_config_error(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(": : : not valid yaml\n")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))

        from marvin.config import InterpolatingYamlSettingsSource
        from marvin.libs.config.base import ConfigError
        from pydantic_settings import BaseSettings

        with pytest.raises(ConfigError, match="Invalid YAML"):
            InterpolatingYamlSettingsSource(BaseSettings)

    def test_non_dict_yaml_raises_config_error(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "list.yaml"
        yaml_file.write_text("- item1\n- item2\n")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))

        from marvin.config import InterpolatingYamlSettingsSource
        from marvin.libs.config.base import ConfigError
        from pydantic_settings import BaseSettings

        with pytest.raises(ConfigError, match="Top-level config must be a mapping"):
            InterpolatingYamlSettingsSource(BaseSettings)

    def test_required_modifier_raises_interpolation_error(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "required.yaml"
        yaml_file.write_text("key: ${MUST_EXIST:?MUST_EXIST is required}\n")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))
        monkeypatch.delenv("MUST_EXIST", raising=False)

        from marvin.config import InterpolatingYamlSettingsSource
        from marvin.libs.config.base import ConfigError
        from marvin.libs.config.interpolation import InterpolationError
        from pydantic_settings import BaseSettings

        with pytest.raises(InterpolationError, match="MUST_EXIST is required"):
            InterpolatingYamlSettingsSource(BaseSettings)
        # InterpolationError is also a ConfigError
        with pytest.raises(ConfigError):
            InterpolatingYamlSettingsSource(BaseSettings)

    def test_interpolated_empty_omits_key_in_source(self, tmp_path, monkeypatch):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("keep: hello\ndrop: ${UNSET_VAR}\n")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))
        monkeypatch.delenv("UNSET_VAR", raising=False)

        from marvin.config import InterpolatingYamlSettingsSource
        from pydantic_settings import BaseSettings

        source = InterpolatingYamlSettingsSource(BaseSettings)
        assert source.init_kwargs.get("keep") == "hello"
        assert "drop" not in source.init_kwargs


    def test_empty_yaml_file_returns_empty(self, tmp_path, monkeypatch):
        """A YAML file with only whitespace/comments yields empty kwargs."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("# just a comment\n")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))

        from marvin.config import InterpolatingYamlSettingsSource
        from pydantic_settings import BaseSettings

        source = InterpolatingYamlSettingsSource(BaseSettings)
        assert source.init_kwargs == {}

    def test_unreadable_yaml_raises_config_error(self, tmp_path, monkeypatch):
        """An unreadable file triggers the OSError branch."""
        yaml_file = tmp_path / "locked.yaml"
        yaml_file.write_text("key: value\n")
        yaml_file.chmod(0o000)
        monkeypatch.setenv("MARVIN_CONFIG_FILE_YAML", str(yaml_file))

        from marvin.config import InterpolatingYamlSettingsSource
        from marvin.libs.config.base import ConfigError
        from pydantic_settings import BaseSettings

        with pytest.raises(ConfigError, match="Cannot read config file"):
            InterpolatingYamlSettingsSource(BaseSettings)

        yaml_file.chmod(0o644)


class TestInterpolatingJsonSettingsSource:
    """End-to-end via InterpolatingJsonSettingsSource."""

    def test_interpolated_json_loads(self, tmp_path, monkeypatch):
        json_file = tmp_path / ".marvin.json"
        json_file.write_text('{"core": {"provider_name": "${_TEST_PROVIDER:-fallback}"}}')
        monkeypatch.setenv("MARVIN_CONFIG_FILE_JSON", str(json_file))
        monkeypatch.setenv("_TEST_PROVIDER", "json_provider")

        from marvin.config import InterpolatingJsonSettingsSource
        from pydantic_settings import BaseSettings

        source = InterpolatingJsonSettingsSource(BaseSettings)
        assert source.init_kwargs.get("core", {}).get("provider_name") == "json_provider"

    def test_invalid_json_raises_config_error(self, tmp_path, monkeypatch):
        json_file = tmp_path / "bad.json"
        json_file.write_text("{not valid json}")
        monkeypatch.setenv("MARVIN_CONFIG_FILE_JSON", str(json_file))

        from marvin.config import InterpolatingJsonSettingsSource
        from marvin.libs.config.base import ConfigError
        from pydantic_settings import BaseSettings

        with pytest.raises(ConfigError, match="Invalid JSON"):
            InterpolatingJsonSettingsSource(BaseSettings)
