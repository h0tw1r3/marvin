import asyncio
from urllib.parse import quote

from httpx import Response, AsyncHTTPTransport, AsyncClient

from marvin.clients.bedrock.schema import BedrockChatRequestSchema, BedrockChatResponseSchema
from marvin.clients.bedrock.types import BedrockHTTPClientProtocol
from marvin.config import settings
from marvin.libs.aws.irsa import assume_irsa_credentials
from marvin.libs.aws.signv4 import sign_aws_v4, AwsSigV4Config, AwsCredentials
from marvin.libs.http.client import HTTPClient
from marvin.libs.http.event_hooks.logger import LoggerEventHook
from marvin.libs.http.handlers import HTTPClientError, handle_http_error
from marvin.libs.http.transports.retry import RetryTransport
from marvin.libs.logger import get_logger


class BedrockHTTPClientError(HTTPClientError):
    pass


class BedrockHTTPClient(HTTPClient, BedrockHTTPClientProtocol):
    def __init__(self, client: AsyncClient) -> None:
        super().__init__(client)
        self._cached_credentials: AwsCredentials | None = None
        self._lock = asyncio.Lock()

    async def _get_credentials(self) -> AwsCredentials:
        # Fast path: credentials already cached.
        if self._cached_credentials is not None:
            return self._cached_credentials

        # Slow path: acquire lock and populate cache exactly once.
        # Both static and IRSA paths are inside the lock so concurrent callers
        # wait rather than racing to call STS.
        async with self._lock:
            if self._cached_credentials is not None:
                return self._cached_credentials

            cfg = settings.llm.http_client
            # Static credentials take precedence. IRSA is used when no static
            # credentials are configured.
            if cfg.access_key and cfg.secret_key:
                self._cached_credentials = AwsCredentials(
                    access_key=cfg.access_key,
                    secret_key=cfg.secret_key,
                    session_token=cfg.session_token,
                )
            else:
                # Delegates fully to assume_irsa_credentials, which validates env vars
                # and raises IRSACredentialsError with actionable messages if anything
                # is missing.
                self._cached_credentials = await assume_irsa_credentials(
                    region=cfg.region,
                    verify=cfg.verify,
                    proxy_url=str(cfg.proxy_url_value) if cfg.proxy_url_value else None,
                    timeout=cfg.timeout,
                )

        return self._cached_credentials

    @handle_http_error(client="BedrockHTTPClient", exception=BedrockHTTPClientError)
    async def chat_api(self, request: BedrockChatRequestSchema) -> Response:
        body = request.model_dump_json(exclude_none=True)
        model = quote(settings.llm.meta.model, safe="-._~/")

        route = f"/model/{model}/invoke"
        api_url = settings.llm.http_client.api_url_value.rstrip('/')
        full_url = f"{api_url}{route}"

        credentials = await self._get_credentials()

        return await self.post(
            url=route,
            headers=sign_aws_v4(
                url=full_url,
                body=body,
                method="POST",
                aws_config=AwsSigV4Config(
                    region=settings.llm.http_client.region,
                    service="bedrock"
                ),
                aws_credentials=credentials,
            ),
            content=body
        )

    async def chat(self, request: BedrockChatRequestSchema) -> BedrockChatResponseSchema:
        response = await self.chat_api(request)
        return BedrockChatResponseSchema.model_validate_json(response.text)


def get_bedrock_http_client() -> BedrockHTTPClient:
    logger = get_logger("BEDROCK_HTTP_CLIENT")
    logger_event_hook = LoggerEventHook(logger=logger)

    retry_transport = RetryTransport(
        logger=logger,
        transport=AsyncHTTPTransport(
            proxy=settings.llm.http_client.proxy_url_value,
            verify=settings.llm.http_client.verify,
        )
    )

    client = AsyncClient(
        verify=settings.llm.http_client.verify,
        timeout=settings.llm.http_client.timeout,
        headers={"Content-Type": "application/json"},
        base_url=settings.llm.http_client.api_url_value,
        transport=retry_transport,
        event_hooks={
            "request": [logger_event_hook.request],
            "response": [logger_event_hook.response],
        },
    )

    return BedrockHTTPClient(client=client)
