from typing import Any

import pytest
from pydantic import HttpUrl, SecretStr

from marvin.clients.openrouter.schema import (
    OpenRouterUsageSchema,
    OpenRouterChoiceSchema,
    OpenRouterMessageSchema,
    OpenRouterChatRequestSchema,
    OpenRouterChatResponseSchema,
)
from marvin.clients.openrouter.types import OpenRouterHTTPClientProtocol
from marvin.config import settings
from marvin.libs.config.llm.base import OpenRouterLLMConfig
from marvin.libs.config.llm.openrouter import OpenRouterMetaConfig, OpenRouterHTTPClientConfig
from marvin.libs.constants.llm_provider import LLMProvider
from marvin.services.llm.openrouter.client import OpenRouterLLMClient


class FakeOpenRouterHTTPClient(OpenRouterHTTPClientProtocol):
    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.responses = responses or {}

    async def chat(self, request: OpenRouterChatRequestSchema) -> OpenRouterChatResponseSchema:
        self.calls.append(("chat", {"request": request}))
        return self.responses.get(
            "chat",
            OpenRouterChatResponseSchema(
                usage=OpenRouterUsageSchema(total_tokens=12, prompt_tokens=5, completion_tokens=7),
                choices=[
                    OpenRouterChoiceSchema(
                        message=OpenRouterMessageSchema(
                            role="assistant",
                            content="FAKE_OPENROUTER_RESPONSE"
                        )
                    )
                ],
            ),
        )


@pytest.fixture
def fake_openrouter_http_client() -> FakeOpenRouterHTTPClient:
    return FakeOpenRouterHTTPClient()


@pytest.fixture
def openrouter_llm_client(
        monkeypatch: pytest.MonkeyPatch,
        fake_openrouter_http_client: FakeOpenRouterHTTPClient
) -> OpenRouterLLMClient:
    monkeypatch.setattr(
        "marvin.services.llm.openrouter.client.get_openrouter_http_client",
        lambda: fake_openrouter_http_client,
    )
    return OpenRouterLLMClient()


@pytest.fixture
def openrouter_http_client_config(monkeypatch: pytest.MonkeyPatch):
    fake_config = OpenRouterLLMConfig(
        meta=OpenRouterMetaConfig(),
        provider=LLMProvider.OPENROUTER,
        http_client=OpenRouterHTTPClientConfig(
            timeout=10,
            api_url=HttpUrl("https://openrouter.ai/api/v1"),
            api_token=SecretStr("fake-token"),
        )
    )
    monkeypatch.setattr(settings, "llm", fake_config)
