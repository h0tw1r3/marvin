import base64

import pytest
from httpx import Response, Request
from pydantic import SecretStr

from marvin import config
from marvin.clients.gitlab.tools import gitlab_has_next_page, build_gitlab_headers
from marvin.libs.config.token_type import TokenType


def make_response(headers: dict) -> Response:
    return Response(
        request=Request("GET", "http://gitlab.test"),
        headers=headers,
        status_code=200,
    )


def test_gitlab_has_next_page_true():
    resp = make_response({"X-Next-Page": "2"})
    assert gitlab_has_next_page(resp) is True


def test_gitlab_has_next_page_false_empty():
    resp = make_response({"X-Next-Page": ""})
    assert gitlab_has_next_page(resp) is False


def test_gitlab_has_next_page_false_missing():
    resp = make_response({})
    assert gitlab_has_next_page(resp) is False


# ---------------------------------------------------------------------------
# build_gitlab_headers
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("gitlab_http_client_config")
def test_build_gitlab_headers_bearer(monkeypatch: pytest.MonkeyPatch):
    """Should build a Bearer Authorization header when token type is BEARER."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BEARER)

    headers = build_gitlab_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("gitlab_http_client_config")
def test_build_gitlab_headers_basic(monkeypatch: pytest.MonkeyPatch):
    """Should build a Basic Authorization header when token type is BASIC."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BASIC)

    headers = build_gitlab_headers()

    assert headers == {"Authorization": "Basic fake-token"}


@pytest.mark.usefixtures("gitlab_http_client_config")
def test_build_gitlab_headers_auto_resolves_bearer(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a plain token should fall back to Bearer."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    # The fixture default "fake-token" is not a Base64-encoded user:pass pair.

    headers = build_gitlab_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("gitlab_http_client_config")
def test_build_gitlab_headers_auto_resolves_basic(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a Base64-encoded ``username:password`` token should use Basic."""
    encoded = base64.b64encode(b"user:apppassword").decode("ascii")
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token", SecretStr(encoded))

    headers = build_gitlab_headers()

    assert headers == {"Authorization": f"Basic {encoded}"}
