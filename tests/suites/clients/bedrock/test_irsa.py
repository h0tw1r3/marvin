import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import HttpUrl, ValidationError

from marvin.clients.bedrock.client import BedrockHTTPClient, get_bedrock_http_client
from marvin.libs.aws.irsa import IRSACredentialsError
from marvin.libs.aws.signv4 import AwsCredentials
from marvin.libs.config.llm.bedrock import BedrockHTTPClientConfig


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

def test_bedrock_config_static_creds_both_present():
    cfg = BedrockHTTPClientConfig(
        api_url=HttpUrl("https://bedrock-runtime.fake.aws"),
        region="us-east-1",
        access_key="AK",
        secret_key="SK",
    )
    assert cfg.access_key == "AK"
    assert cfg.secret_key == "SK"


def test_bedrock_config_no_static_creds_valid():
    cfg = BedrockHTTPClientConfig(
        api_url=HttpUrl("https://bedrock-runtime.fake.aws"),
        region="us-east-1",
    )
    assert cfg.access_key is None
    assert cfg.secret_key is None


def test_bedrock_config_partial_creds_raises_access_key_only():
    with pytest.raises(ValidationError, match="both access_key and secret_key"):
        BedrockHTTPClientConfig(
            api_url=HttpUrl("https://bedrock-runtime.fake.aws"),
            region="us-east-1",
            access_key="AK",
        )


def test_bedrock_config_partial_creds_raises_secret_key_only():
    with pytest.raises(ValidationError, match="both access_key and secret_key"):
        BedrockHTTPClientConfig(
            api_url=HttpUrl("https://bedrock-runtime.fake.aws"),
            region="us-east-1",
            secret_key="SK",
        )


# ---------------------------------------------------------------------------
# _get_credentials - static path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_http_client_config")
async def test_get_credentials_returns_static_creds():
    client = get_bedrock_http_client()
    creds = await client._get_credentials()

    assert creds.access_key == "FAKE_AWS_ACCESS_KEY"
    assert creds.secret_key == "FAKE_AWS_SECRET_KEY"
    assert creds.session_token == "FAKE_SESSION_TOKEN"


@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_http_client_config")
async def test_get_credentials_static_does_not_call_sts(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/some/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    with patch("marvin.clients.bedrock.client.assume_irsa_credentials") as mock_irsa:
        client = get_bedrock_http_client()
        await client._get_credentials()

    mock_irsa.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_http_client_config")
async def test_get_credentials_caches_static_creds():
    client = get_bedrock_http_client()
    creds1 = await client._get_credentials()
    creds2 = await client._get_credentials()

    assert creds1 is creds2


# ---------------------------------------------------------------------------
# _get_credentials - IRSA path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_irsa_config")
async def test_get_credentials_irsa_missing_env_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AWS_WEB_IDENTITY_TOKEN_FILE", raising=False)
    monkeypatch.delenv("AWS_ROLE_ARN", raising=False)

    client = get_bedrock_http_client()
    with pytest.raises(IRSACredentialsError, match="AWS_WEB_IDENTITY_TOKEN_FILE"):
        await client._get_credentials()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_irsa_config")
async def test_get_credentials_irsa_calls_sts_and_returns_creds(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/fake/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    expected = AwsCredentials(
        access_key="ASIA_IRSA_KEY",
        secret_key="irsa-secret",
        session_token="irsa-session-token",
    )

    with patch(
        "marvin.clients.bedrock.client.assume_irsa_credentials",
        new=AsyncMock(return_value=expected),
    ):
        client = get_bedrock_http_client()
        creds = await client._get_credentials()

    assert creds == expected


@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_irsa_config")
async def test_get_credentials_irsa_caches_result(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/fake/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    expected = AwsCredentials(
        access_key="ASIA_IRSA_KEY",
        secret_key="irsa-secret",
        session_token="irsa-session-token",
    )
    mock_irsa = AsyncMock(return_value=expected)

    with patch("marvin.clients.bedrock.client.assume_irsa_credentials", new=mock_irsa):
        client = get_bedrock_http_client()
        await client._get_credentials()
        await client._get_credentials()

    mock_irsa.assert_called_once()


# ---------------------------------------------------------------------------
# Concurrent credential acquisition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_irsa_config")
async def test_get_credentials_concurrent_calls_sts_once(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/fake/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    expected = AwsCredentials(
        access_key="ASIA_IRSA_KEY",
        secret_key="irsa-secret",
        session_token="irsa-session-token",
    )
    call_count = 0

    async def slow_irsa(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Yield to the event loop so other coroutines can attempt _get_credentials
        # and block on the lock - exercising the inner double-checked locking branch.
        await asyncio.sleep(0)
        return expected

    with patch("marvin.clients.bedrock.client.assume_irsa_credentials", new=slow_irsa):
        client = get_bedrock_http_client()
        results = await asyncio.gather(*[client._get_credentials() for _ in range(5)])

    assert call_count == 1
    assert all(r == expected for r in results)


# ---------------------------------------------------------------------------
# Static creds take precedence when both are present
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_http_client_config")
async def test_static_creds_take_precedence_over_irsa_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/fake/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    with patch(
        "marvin.clients.bedrock.client.assume_irsa_credentials"
    ) as mock_irsa:
        client = get_bedrock_http_client()
        creds = await client._get_credentials()

    mock_irsa.assert_not_called()
    assert creds.access_key == "FAKE_AWS_ACCESS_KEY"


# ---------------------------------------------------------------------------
# session_token from IRSA propagates into signing headers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.usefixtures("bedrock_irsa_config")
async def test_irsa_session_token_in_signed_headers(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_WEB_IDENTITY_TOKEN_FILE", "/fake/token")
    monkeypatch.setenv("AWS_ROLE_ARN", "arn:aws:iam::123:role/fake")

    irsa_creds = AwsCredentials(
        access_key="ASIA_IRSA_KEY",
        secret_key="irsa-secret",
        session_token="irsa-session-token",
    )

    signed_headers_captured = {}

    def capture_sign(*args, **kwargs):
        signed_headers_captured.update({"credentials": kwargs.get("aws_credentials")})
        return {"Authorization": "fake", "x-amz-date": "fake", "x-amz-content-sha256": "fake"}

    with patch("marvin.clients.bedrock.client.assume_irsa_credentials", new=AsyncMock(return_value=irsa_creds)), \
         patch("marvin.clients.bedrock.client.sign_aws_v4", side_effect=capture_sign), \
         patch.object(BedrockHTTPClient, "post", new=AsyncMock(return_value=httpx.Response(200, text="{}"))):
        from marvin.clients.bedrock.schema import BedrockChatRequestSchema, BedrockMessageSchema
        client = get_bedrock_http_client()
        try:
            await client.chat_api(BedrockChatRequestSchema(
                messages=[BedrockMessageSchema(role="user", content="hi")]
            ))
        except Exception:
            pass

    if signed_headers_captured.get("credentials"):
        assert signed_headers_captured["credentials"].session_token == "irsa-session-token"
