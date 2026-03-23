from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.llm.meta import LLMMetaConfig


class OpenRouterMetaConfig(LLMMetaConfig):
    model: str = "openai/gpt-4o-mini"
    title: str | None = None
    referer: str | None = None


class OpenRouterHTTPClientConfig(HTTPClientWithTokenConfig):
    pass
