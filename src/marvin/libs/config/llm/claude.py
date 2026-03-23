from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.llm.meta import LLMMetaConfig


class ClaudeMetaConfig(LLMMetaConfig):
    model: str = "claude-3-sonnet"


class ClaudeHTTPClientConfig(HTTPClientWithTokenConfig):
    api_version: str = "2023-06-01"
