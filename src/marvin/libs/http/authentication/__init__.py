import base64
import binascii
import re

from marvin.libs.config.token_type import TokenType


def build_azure_devops_pat_credentials(token: str) -> str:
    """Encode an Azure DevOps PAT as Base64 ``:<token>`` for Basic auth.

    Azure DevOps PAT convention: empty username, PAT as the password.
    The resulting string is passed directly in the ``Authorization: Basic``
    header value.
    """
    return base64.b64encode(f":{token}".encode()).decode("ascii")


def build_authorization_header(token_type: TokenType, token_value: str) -> dict[str, str]:
    """Build an ``Authorization`` header dict for Bearer/Basic auth.

    If ``token_type`` is ``AUTO``, the type is resolved first via
    :func:`detect_token_type`.  Pass explicit ``BEARER`` or ``BASIC``
    to bypass detection.
    """
    if token_type is TokenType.AUTO:
        token_type = detect_token_type(token_value)

    match token_type:
        case TokenType.BEARER:
            return {"Authorization": f"Bearer {token_value}"}
        case TokenType.BASIC:
            return {"Authorization": f"Basic {token_value}"}
        case _:
            raise ValueError(f"Unsupported token type: {token_type}")


def detect_token_type(token: str) -> TokenType:
    """Resolve ``TokenType.AUTO`` to either ``BEARER`` or ``BASIC``.

    The heuristic is intentionally strict to minimise false positives:

    1. Attempt ``base64.b64decode(validate=True)`` -- rejects any value
       that contains characters outside the standard Base64 alphabet.
    2. Decode the bytes as UTF-8.
    3. Match the decoded string against ``^[^\\s:]+:[^\\s]+$`` --
       requires a non-empty username (no colons), at least one colon
       separator, a non-empty password (may itself contain colons), and
       no whitespace anywhere.

    If all three checks pass the token is treated as a pre-encoded
    Basic credential and ``BASIC`` is returned.  Any failure (bad
    Base64, non-UTF-8 bytes, pattern mismatch) returns ``BEARER``.

    This is best-effort.  Set ``api_token_type`` explicitly to
    ``BEARER`` or ``BASIC`` to bypass detection entirely.
    """
    try:
        decoded = base64.b64decode(token, validate=True).decode("utf-8")
        if re.match(r"^[^\s:]+:[^\s]+$", decoded):
            return TokenType.BASIC
    except (binascii.Error, UnicodeDecodeError):
        pass
    return TokenType.BEARER
