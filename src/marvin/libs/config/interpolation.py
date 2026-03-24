"""Docker Compose–style string interpolation for config file values.

Implements the interpolation grammar from the Docker Compose specification
(https://docs.docker.com/reference/compose-file/interpolation/) for use with
parsed YAML/JSON config structures. Only ``os.environ`` (or an injected mapping)
is consulted — ``.env`` file loading is a separate concern.

Intentional deltas from Compose:
  - Dict values that become empty via interpolation are **omitted** (treated as
    unset) so pydantic-settings can fall through to defaults or lower-priority
    sources.  List items are preserved as ``""`` to avoid shifting indices.
  - Malformed patterns (unmatched ``${``, lone ``$``, etc.) are preserved as
    literal text rather than raising errors.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

from loguru import logger

from marvin.libs.config.base import ConfigError

_OMIT = object()
"""Sentinel returned by the expansion walk to signal that a dict key should be
removed from the output (interpolation resolved to empty string)."""


class InterpolationError(ConfigError):
    """Raised when a required-modifier (``${VAR:?msg}`` / ``${VAR?msg}``) fails
    because the referenced variable is unset or empty."""


# =============================================================================
# Name scanning helpers
# =============================================================================

def _is_name_start(ch: str) -> bool:
    return ch == "_" or ch.isalpha()


def _scan_name(s: str, start: int) -> tuple[str, int]:
    """Scan a variable name starting at *start*.  Returns ``(name, end_index)``."""
    i = start
    while i < len(s) and (s[i] == "_" or s[i].isalnum()):
        i += 1
    return s[start:i], i


# =============================================================================
# Warning helper
# =============================================================================

def _warn_unresolved(name: str, warned: set[str]) -> None:
    """Emit a warning for an unresolved variable, at most once per name."""
    if name not in warned:
        warned.add(name)
        logger.warning("Unresolved variable: {}", name)


# =============================================================================
# Shared token resolution
# =============================================================================

def _resolve_dollar(
    s: str,
    i: int,
    env: Mapping[str, str],
    warned: set[str],
) -> tuple[str, int]:
    """Resolve a ``$`` token at position *i*.

    Returns ``(resolved_text, new_index)`` covering ``$$``, ``${…}``,
    unbraced ``$NAME``, and literal ``$`` fallback.
    """
    if i + 1 >= len(s):
        return "$", i + 1

    next_ch = s[i + 1]

    if next_ch == "$":
        return "$", i + 2

    if next_ch == "{":
        parsed, end = _parse_braced(s, i + 2, env, warned)
        if parsed is None:
            return "${", i + 2
        return parsed, end

    if _is_name_start(next_ch):
        name, end = _scan_name(s, i + 1)
        value = env.get(name)
        if value is None:
            _warn_unresolved(name, warned)
            return "", end
        return value, end

    return "$", i + 1


# =============================================================================
# String-level interpolation
# =============================================================================

def interpolate_compose(
    s: str,
    *,
    env: Mapping[str, str] | None = None,
    _warned: set[str] | None = None,
) -> str:
    """Interpolate *s* using Docker Compose–style ``$VAR`` / ``${VAR}`` syntax.

    Parameters
    ----------
    s:
        The raw string potentially containing interpolation tokens.
    env:
        Variable mapping (defaults to ``os.environ``).
    _warned:
        Mutable set tracking variable names already warned about in this
        expansion operation.  Callers should not pass this directly; it is
        managed by :func:`expand_env_in_structure`.

    Returns
    -------
    str
        The interpolated result.  Always a string — omission decisions are
        made by the structure-walking layer, not here.
    """
    if env is None:
        env = os.environ
    if _warned is None:
        _warned = set()

    result: list[str] = []
    i = 0
    length = len(s)

    while i < length:
        if s[i] == "$":
            text, i = _resolve_dollar(s, i, env, _warned)
            result.append(text)
        else:
            result.append(s[i])
            i += 1

    return "".join(result)


# =============================================================================
# Braced-expression parser  ${...}
# =============================================================================

def _parse_braced(
    s: str,
    start: int,
    env: Mapping[str, str],
    warned: set[str],
) -> tuple[str | None, int]:
    """Parse content inside ``${`` … ``}``, starting at *start*.

    Returns ``(interpolated_value, index_past_closing_brace)`` on success, or
    ``(None, 0)`` when the expression is malformed (no closing brace, empty
    variable name, etc.).
    """
    if start >= len(s) or not _is_name_start(s[start]):
        return None, 0

    name, pos = _scan_name(s, start)

    if pos >= len(s):
        return None, 0

    ch = s[pos]

    # Simple form: ${VAR}
    if ch == "}":
        value = env.get(name)
        if value is None:
            _warn_unresolved(name, warned)
            return "", pos + 1
        return value, pos + 1

    # Modifier forms: check for :- :+ :? - + ?
    colon = False
    if ch == ":":
        colon = True
        pos += 1
        if pos >= len(s):
            return None, 0
        ch = s[pos]

    if ch in ("-", "+", "?"):
        modifier = ch
        pos += 1
        operand, end = _collect_operand(s, pos, env, warned)
        if end == -1:
            return None, 0
        return _apply_modifier(name, modifier, colon, operand, env), end + 1

    return None, 0


def _collect_operand(
    s: str,
    start: int,
    env: Mapping[str, str],
    warned: set[str],
) -> tuple[str, int]:
    """Collect the operand text for a modifier, resolving nested ``${…}``.

    Returns ``(resolved_operand, index_of_closing_brace)`` or
    ``("", -1)`` on failure.

    Limitation: a literal ``}`` in the operand (outside a nested ``${…}``)
    will be treated as the closing brace of the outer expression.  This
    matches Docker Compose behavior — operands cannot contain unescaped
    ``}``.  In practice config default values almost never include raw
    braces.
    """
    parts: list[str] = []
    i = start

    while i < len(s):
        ch = s[i]

        if ch == "}":
            return "".join(parts), i
        if ch == "$":
            text, i = _resolve_dollar(s, i, env, warned)
            parts.append(text)
        else:
            parts.append(ch)
            i += 1

    return "", -1


def _apply_modifier(
    name: str,
    modifier: str,
    colon: bool,
    operand: str,
    env: Mapping[str, str],
) -> str:
    """Apply a braced modifier to variable *name*."""
    raw = env.get(name)
    is_set = raw is not None
    is_nonempty = is_set and raw != ""

    if modifier == "-":
        use_default = (not is_nonempty) if colon else (not is_set)
        return operand if use_default else cast("str", raw)

    if modifier == "+":
        use_replacement = is_nonempty if colon else is_set
        return operand if use_replacement else ""

    if modifier == "?":
        should_fail = (not is_nonempty) if colon else (not is_set)
        if should_fail:
            raise InterpolationError(operand.strip() or name)
        return cast("str", raw)

    raise AssertionError(f"Unknown modifier: {modifier!r}")


# =============================================================================
# Structure-level expansion
# =============================================================================

def expand_env_in_structure(
    obj: Any,
    *,
    env: Mapping[str, str] | None = None,
) -> Any:
    """Recursively walk a parsed config structure and interpolate string values.

    Designed for structures produced by ``yaml.safe_load`` / ``json.loads``
    (root expected to be ``dict``).  Non-dict/list containers (e.g. tuples)
    are returned unchanged.

    Dict values that resolve to ``""`` **due to interpolation** are omitted
    from the returned dict so pydantic-settings can fall through to defaults.
    List items that resolve to ``""`` are preserved to avoid index shifts.
    Literal ``""`` values (strings with no interpolation tokens) are kept as-is.

    Parameters
    ----------
    env:
        Variable mapping.  Defaults to ``os.environ`` when ``None``.  Pass an
        empty ``{}`` to explicitly use no variables.
    """
    warned: set[str] = set()
    resolved_env = env if env is not None else os.environ
    return _expand(obj, env=resolved_env, warned=warned, in_dict_value=False)


def _expand(
    obj: Any,
    *,
    env: Mapping[str, str],
    warned: set[str],
    in_dict_value: bool,
) -> Any:
    """Internal recursive expansion.

    *in_dict_value* is True when expanding a value that belongs to a dict key.
    When an interpolated string resolves to ``""`` in dict-value context, the
    sentinel ``_OMIT`` is returned so the calling dict-walk can drop the key.
    """
    if isinstance(obj, str):
        if "$" not in obj:
            return obj
        result = interpolate_compose(obj, env=env, _warned=warned)
        if result == "" and in_dict_value:
            return _OMIT
        return result

    if isinstance(obj, dict):
        expanded: dict[str, Any] = {}
        for key, value in obj.items():
            new_value = _expand(value, env=env, warned=warned, in_dict_value=True)
            if new_value is not _OMIT:
                expanded[key] = new_value
        return expanded

    if isinstance(obj, list):
        return [
            _expand(item, env=env, warned=warned, in_dict_value=False)
            for item in obj
        ]

    return obj
