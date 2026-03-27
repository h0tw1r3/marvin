from unittest.mock import AsyncMock, patch

import httpx
import pytest

from marvin.libs.aws.irsa import (
    IRSACredentialsError,
    _extract_aws_error,
    _parse_sts_response,
    _sts_endpoint,
    assume_irsa_credentials,
)
from marvin.libs.aws.signv4 import AwsCredentials


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_STS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <AssumeRoleWithWebIdentityResult>
    <Credentials>
      <AccessKeyId>ASIA_FAKE_KEY</AccessKeyId>
      <SecretAccessKey>fake/secret/key</SecretAccessKey>
      <SessionToken>fake-session-token-abc123</SessionToken>
      <Expiration>2099-01-01T00:00:00Z</Expiration>
    </Credentials>
  </AssumeRoleWithWebIdentityResult>
</AssumeRoleWithWebIdentityResponse>"""


# ---------------------------------------------------------------------------
# _parse_sts_response
# ---------------------------------------------------------------------------

def test_parse_sts_response_returns_credentials():
    creds = _parse_sts_response(_VALID_STS_XML)

    assert creds == AwsCredentials(
        access_key="ASIA_FAKE_KEY",
        secret_key="fake/secret/key",
        session_token="fake-session-token-abc123",
    )


def test_parse_sts_response_invalid_xml():
    with pytest.raises(IRSACredentialsError, match="could not be parsed as XML"):
        _parse_sts_response("not xml at all <<<")


def test_parse_sts_response_missing_credentials_element():
    xml = """<Response xmlns="https://sts.amazonaws.com/doc/2011-06-15/"><Other/></Response>"""
    with pytest.raises(IRSACredentialsError, match="Credentials element"):
        _parse_sts_response(xml)


def test_parse_sts_response_wrong_namespace():
    # Bare tag names without namespace - should fail to find Credentials
    xml = """<?xml version="1.0"?>
<AssumeRoleWithWebIdentityResponse>
  <AssumeRoleWithWebIdentityResult>
    <Credentials>
      <AccessKeyId>AK</AccessKeyId>
      <SecretAccessKey>SK</SecretAccessKey>
      <SessionToken>ST</SessionToken>
    </Credentials>
  </AssumeRoleWithWebIdentityResult>
</AssumeRoleWithWebIdentityResponse>"""
    with pytest.raises(IRSACredentialsError, match="Credentials element"):
        _parse_sts_response(xml)


def test_parse_sts_response_missing_field():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<AssumeRoleWithWebIdentityResponse xmlns="https://sts.amazonaws.com/doc/2011-06-15/">
  <AssumeRoleWithWebIdentityResult>
    <Credentials>
      <AccessKeyId>AK</AccessKeyId>
      <SecretAccessKey>SK</SecretAccessKey>
    </Credentials>
  </AssumeRoleWithWebIdentityResult>
</AssumeRoleWithWebIdentityResponse>"""
    with pytest.raises(IRSACredentialsError, match="SessionToken"):
        _parse_sts_response(xml)


# ---------------------------------------------------------------------------
# _extract_aws_error
# ---------------------------------------------------------------------------

def test_extract_aws_error_code_and_message():
    xml = "<Error><Code>AccessDenied</Code><Message>Not authorized</Message></Error>"
    assert _extract_aws_error(xml) == " (AccessDenied: Not authorized)"


def test_extract_aws_error_code_only():
    xml = "<Error><Code>InvalidIdentityToken</Code></Error>"
    assert _extract_aws_error(xml) == " (InvalidIdentityToken)"


def test_extract_aws_error_no_code_or_message():
    xml = "<Error><Other>stuff</Other></Error>"
    assert _extract_aws_error(xml) == ""


def test_extract_aws_error_invalid_xml():
    assert _extract_aws_error("not xml <<<") == ""


# ---------------------------------------------------------------------------
# _sts_endpoint - endpoint selection
# ---------------------------------------------------------------------------

def test_sts_endpoint_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL_STS", raising=False)
    assert _sts_endpoint("us-east-1") == "https://sts.us-east-1.amazonaws.com/"


def test_sts_endpoint_govcloud(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL_STS", raising=False)
    assert _sts_endpoint("us-gov-west-1") == "https://sts.us-gov-west-1.amazonaws.com/"


def test_sts_endpoint_fips_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL_STS", "https://sts-fips.us-east-1.amazonaws.com")
    assert _sts_endpoint("us-east-1") == "https://sts-fips.us-east-1.amazonaws.com/"


def test_sts_endpoint_override_normalizes_trailing_slash(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL_STS", "https://sts-fips.us-east-1.amazonaws.com/")
    assert _sts_endpoint("us-east-1") == "https://sts-fips.us-east-1.amazonaws.com/"


def test_sts_endpoint_override_ignores_region(monkeypatch: pytest.MonkeyPatch):
    # When override is set, the region argument is ignored
    monkeypatch.setenv("AWS_ENDPOINT_URL_STS", "https://sts-fips.us-west-2.amazonaws.com")
    assert _sts_endpoint("us-east-1") == "https://sts-fips.us-west-2.amazonaws.com/"


def test_sts_endpoint_china_without_override_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_ENDPOINT_URL_STS", raising=False)
    with pytest.raises(IRSACredentialsError, match="China region"):
        _sts_endpoint("cn-north-1")


def test_sts_endpoint_china_with_override_succeeds(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL_STS", "https://sts.cn-north-1.amazonaws.com.cn")
    assert _sts_endpoint("cn-north-1") == "https://sts.cn-north-1.amazonaws.com.cn/"


# ---------------------------------------------------------------------------
# assume_irsa_credentials - env / file validation
# ---------------------------------------------------------------------------

def test_assume_irsa_credentials_missing_token_file_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_WEB_IDENTITY_TOKEN_FILE", raising=False)
    monkeypatch.delenv("AWS_ROLE_ARN", raising=False)

    with pytest.raises(IRSACredentialsError, match="AWS_WEB_IDENTITY_TOKEN_FILE"):
        import asyncio
        asyncio.run(assume_irsa_credentials("us-east-1"))


def test_assume_irsa_credentials_missing_role_arn(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.delenv("AWS_ROLE_ARN", raising=False)

    with pytest.raises(IRSACredentialsError, match="AWS_ROLE_ARN"):
        import asyncio
        asyncio.run(assume_irsa_credentials("us-east-1"))


def test_assume_irsa_credentials_unreadable_token_file(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/nonexistent/path/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")

    with pytest.raises(IRSACredentialsError, match="Could not read web identity token file"):
        import asyncio
        asyncio.run(assume_irsa_credentials("us-east-1"))


# ---------------------------------------------------------------------------
# assume_irsa_credentials - HTTP / full flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assume_irsa_credentials_success(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")
    monkeypatch.delenv("AWS_ROLE_SESSION_NAME", raising=False)

    fake_response = httpx.Response(200, text=_VALID_STS_XML)

    with patch("marvin.libs.aws.irsa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_client

        creds = await assume_irsa_credentials("us-east-1")

    assert creds.access_key == "ASIA_FAKE_KEY"
    assert creds.secret_key == "fake/secret/key"
    assert creds.session_token == "fake-session-token-abc123"

    # Verify POST was used (not GET)
    call_kwargs = mock_client.post.call_args
    assert call_kwargs is not None
    assert "application/x-www-form-urlencoded" in call_kwargs.kwargs.get("headers", {}).get("Content-Type", "")

    # Verify token is in the POST body, not the URL query string
    call_url = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("url", "")
    assert "fake-jwt-token" not in call_url


@pytest.mark.asyncio
async def test_assume_irsa_credentials_transport_error(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")
    monkeypatch.delenv("AWS_ROLE_SESSION_NAME", raising=False)

    with patch("marvin.libs.aws.irsa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client_cls.return_value = mock_client

        with pytest.raises(IRSACredentialsError, match="STS request failed: ConnectError: connection refused"):
            await assume_irsa_credentials("us-east-1")


@pytest.mark.asyncio
async def test_assume_irsa_credentials_sts_non_200(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")
    monkeypatch.delenv("AWS_ROLE_SESSION_NAME", raising=False)

    fake_response = httpx.Response(400, text="<Error><Code>InvalidIdentityToken</Code></Error>")

    with patch("marvin.libs.aws.irsa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_client

        with pytest.raises(IRSACredentialsError, match="HTTP 400"):
            await assume_irsa_credentials("us-east-1")


@pytest.mark.asyncio
async def test_assume_irsa_credentials_session_name_uses_pid(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")
    monkeypatch.delenv("AWS_ROLE_SESSION_NAME", raising=False)

    fake_response = httpx.Response(200, text=_VALID_STS_XML)

    with patch("marvin.libs.aws.irsa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_client

        await assume_irsa_credentials("us-east-1")

    body_bytes = mock_client.post.call_args.kwargs.get("content", b"")
    from urllib.parse import parse_qs
    params = parse_qs(body_bytes.decode())
    session_name = params["RoleSessionName"][0]
    assert session_name.startswith("marvin-")
    assert session_name[len("marvin-"):].isdigit()


@pytest.mark.asyncio
async def test_assume_irsa_credentials_session_name_override(monkeypatch: pytest.MonkeyPatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("fake-jwt-token")

    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123456789:role/fake-role")
    monkeypatch.setenv("AWS_ROLE_SESSION_NAME", "custom-session")

    fake_response = httpx.Response(200, text=_VALID_STS_XML)

    with patch("marvin.libs.aws.irsa.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fake_response)
        mock_client_cls.return_value = mock_client

        await assume_irsa_credentials("us-east-1")

    body_bytes = mock_client.post.call_args.kwargs.get("content", b"")
    from urllib.parse import parse_qs
    params = parse_qs(body_bytes.decode())
    assert params["RoleSessionName"][0] == "custom-session"
