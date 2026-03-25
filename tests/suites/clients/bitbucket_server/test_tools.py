import base64
import json

import pytest
from httpx import Response, Request
from pydantic import SecretStr

from marvin import config
from marvin.clients.bitbucket_server.tools import bitbucket_server_has_next_page, build_bitbucket_server_headers
from marvin.libs.config.token_type import TokenType


def make_response(data: dict) -> Response:
    """Helper to create a fake HTTPX Response with given JSON data."""
    return Response(
        status_code=200,
        content=json.dumps(data).encode(),
        request=Request("GET", "http://bitbucket-server.test"),
    )


def test_bitbucket_server_has_next_page_true_when_not_last():
    """Should return True if isLastPage=False (i.e., more pages exist)."""
    resp = make_response({"isLastPage": False})
    assert bitbucket_server_has_next_page(resp) is True


def test_bitbucket_server_has_next_page_false_when_last_page():
    """Should return False if isLastPage=True (last page reached)."""
    resp = make_response({"isLastPage": True})
    assert bitbucket_server_has_next_page(resp) is False


def test_bitbucket_server_has_next_page_false_when_missing():
    """Should default to False if isLastPage key is missing (treated as last page)."""
    resp = make_response({})
    assert bitbucket_server_has_next_page(resp) is False


def test_bitbucket_server_has_next_page_false_when_invalid_type():
    """Should handle invalid non-bool values gracefully."""
    resp = make_response({"isLastPage": "not-a-bool"})
    assert bitbucket_server_has_next_page(resp) is False


# ---------------------------------------------------------------------------
# build_bitbucket_server_headers
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("bitbucket_server_http_client_config")
def test_build_bitbucket_server_headers_bearer(monkeypatch: pytest.MonkeyPatch):
    """Should build a Bearer Authorization header when token type is BEARER."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BEARER)

    headers = build_bitbucket_server_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("bitbucket_server_http_client_config")
def test_build_bitbucket_server_headers_basic(monkeypatch: pytest.MonkeyPatch):
    """Should build a Basic Authorization header when token type is BASIC."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BASIC)

    headers = build_bitbucket_server_headers()

    assert headers == {"Authorization": "Basic fake-token"}


@pytest.mark.usefixtures("bitbucket_server_http_client_config")
def test_build_bitbucket_server_headers_auto_resolves_bearer(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a plain token should fall back to Bearer."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    # The fixture default "fake-token" is not a Base64-encoded user:pass pair.

    headers = build_bitbucket_server_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("bitbucket_server_http_client_config")
def test_build_bitbucket_server_headers_auto_resolves_basic(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a Base64-encoded ``username:password`` token should use Basic."""
    encoded = base64.b64encode(b"user:apppassword").decode("ascii")
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token", SecretStr(encoded))

    headers = build_bitbucket_server_headers()

    assert headers == {"Authorization": f"Basic {encoded}"}
