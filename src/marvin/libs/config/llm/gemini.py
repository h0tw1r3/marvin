from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.llm.meta import LLMMetaConfig


class GeminiMetaConfig(LLMMetaConfig):
    model: str = "gemini-2.0-pro"


class GeminiHTTPClientConfig(HTTPClientWithTokenConfig):
    pass
