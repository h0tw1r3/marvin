import base64

import pytest
from httpx import Response, Request
from pydantic import SecretStr

from marvin import config
from marvin.clients.bitbucket_cloud.tools import bitbucket_cloud_has_next_page, build_bitbucket_cloud_headers
from marvin.libs.config.token_type import TokenType


def make_response(data: dict) -> Response:
    return Response(
        json=data,
        request=Request("GET", "http://bitbucket.test"),
        status_code=200,
    )


def test_bitbucket_cloud_has_next_page_true():
    resp = make_response({"next": "https://api.bitbucket.org/2.0/repositories/test/repo?page=2"})
    assert bitbucket_cloud_has_next_page(resp) is True


def test_bitbucket_cloud_has_next_page_false_none():
    resp = make_response({"next": None})
    assert bitbucket_cloud_has_next_page(resp) is False


def test_bitbucket_cloud_has_next_page_false_missing():
    resp = make_response({})
    assert bitbucket_cloud_has_next_page(resp) is False


def test_bitbucket_cloud_has_next_page_false_empty_string():
    resp = make_response({"next": ""})
    assert bitbucket_cloud_has_next_page(resp) is False


# ---------------------------------------------------------------------------
# build_bitbucket_cloud_headers
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("bitbucket_cloud_http_client_config")
def test_build_bitbucket_cloud_headers_bearer(monkeypatch: pytest.MonkeyPatch):
    """Should build a Bearer Authorization header when token type is BEARER."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BEARER)

    headers = build_bitbucket_cloud_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("bitbucket_cloud_http_client_config")
def test_build_bitbucket_cloud_headers_basic(monkeypatch: pytest.MonkeyPatch):
    """Should build a Basic Authorization header when token type is BASIC."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.BASIC)

    headers = build_bitbucket_cloud_headers()

    assert headers == {"Authorization": "Basic fake-token"}


@pytest.mark.usefixtures("bitbucket_cloud_http_client_config")
def test_build_bitbucket_cloud_headers_auto_resolves_bearer(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a plain token should fall back to Bearer."""
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    # The fixture default "fake-token" is not a Base64-encoded user:pass pair.

    headers = build_bitbucket_cloud_headers()

    assert headers == {"Authorization": "Bearer fake-token"}


@pytest.mark.usefixtures("bitbucket_cloud_http_client_config")
def test_build_bitbucket_cloud_headers_auto_resolves_basic(monkeypatch: pytest.MonkeyPatch):
    """AUTO with a Base64-encoded ``username:password`` token should use Basic."""
    encoded = base64.b64encode(b"user:apppassword").decode("ascii")
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token_type", TokenType.AUTO)
    monkeypatch.setattr(config.settings.vcs.http_client, "api_token", SecretStr(encoded))

    headers = build_bitbucket_cloud_headers()

    assert headers == {"Authorization": f"Basic {encoded}"}
