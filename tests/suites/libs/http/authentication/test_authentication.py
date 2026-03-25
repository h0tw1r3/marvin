import base64

import pytest

from marvin.libs.config.token_type import TokenType
from marvin.libs.http.authentication import (
    build_authorization_header,
    build_azure_devops_pat_credentials,
    detect_token_type,
)


# ---------------------------------------------------------------------------
# build_azure_devops_pat_credentials
# ---------------------------------------------------------------------------

def test_build_azure_devops_pat_credentials_encodes_token_with_empty_username():
    token = "my-secret-token"

    result = build_azure_devops_pat_credentials(token)

    expected = base64.b64encode(f":{token}".encode()).decode("ascii")
    assert result == expected


def test_build_azure_devops_pat_credentials_result_is_ascii_string():
    token = "token-123"

    result = build_azure_devops_pat_credentials(token)

    # Basic auth header value must be ASCII
    result.encode("ascii")  # should not raise


def test_build_azure_devops_pat_credentials_with_empty_token():
    token = ""

    result = build_azure_devops_pat_credentials(token)

    expected = base64.b64encode(b":").decode("ascii")
    assert result == expected


# ---------------------------------------------------------------------------
# build_authorization_header
# ---------------------------------------------------------------------------

def test_build_authorization_header_raises_for_unsupported_token_type():
    """A value that passes the AUTO guard but matches no case raises ValueError."""
    from unittest.mock import MagicMock

    # A MagicMock is not TokenType.AUTO (identity check), so it bypasses
    # detect_token_type. It also won't compare equal to BEARER or BASIC in
    # the match, so the catch-all case fires.
    fake_type = MagicMock(spec=TokenType)

    with pytest.raises(ValueError, match="Unsupported token type"):
        build_authorization_header(fake_type, "tok")


# ---------------------------------------------------------------------------
# detect_token_type
# ---------------------------------------------------------------------------

def test_detect_token_type_returns_basic_for_encoded_user_colon_password():
    """Valid Base64-encoded ``username:password`` -> BASIC."""
    encoded = base64.b64encode(b"alice:s3cr3t").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BASIC


def test_detect_token_type_returns_bearer_for_plain_token():
    """A plain token that is not Base64-encoded -> BEARER."""
    result = detect_token_type("ghp_someGitHubToken1234567890abcdef")

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_for_invalid_base64():
    """A string that cannot be decoded as Base64 -> BEARER."""
    result = detect_token_type("not===valid---base64!!!")

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_when_decoded_has_no_colon():
    """Valid Base64, but decoded value has no colon -> BEARER (not a credential pair)."""
    encoded = base64.b64encode(b"nocolonhere").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_when_username_is_empty():
    """Decoded value ``:password`` has an empty username -> BEARER (strict check)."""
    encoded = base64.b64encode(b":password").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_when_password_is_empty():
    """Decoded value ``username:`` has an empty password -> BEARER (strict check)."""
    encoded = base64.b64encode(b"username:").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_when_decoded_contains_whitespace():
    """Whitespace in the decoded value -> BEARER (strict pattern rejects it)."""
    encoded = base64.b64encode(b"user name:pass word").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BEARER


def test_detect_token_type_returns_bearer_for_jwt_like_token():
    """A JWT (contains dots, valid Base64 segments) should not be mistaken for Basic."""
    # Minimal fake JWT - header.payload.signature, each Base64url segment
    jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.signature"

    result = detect_token_type(jwt)

    assert result is TokenType.BEARER


def test_detect_token_type_with_special_chars_in_password():
    """Special characters in the password portion are allowed."""
    encoded = base64.b64encode(b"user:p@ssw0rd!#$").decode("ascii")

    result = detect_token_type(encoded)

    assert result is TokenType.BASIC


def test_detect_token_type_returns_bearer_for_empty_string():
    """Empty token string should fall back to Bearer rather than raise."""
    result = detect_token_type("")

    assert result is TokenType.BEARER
