from pydantic import model_validator

from marvin.libs.config.http import HTTPClientConfig
from marvin.libs.config.llm.meta import LLMMetaConfig


class BedrockMetaConfig(LLMMetaConfig):
    model: str = "anthropic.claude-3-sonnet-20240229-v1:0"


class BedrockHTTPClientConfig(HTTPClientConfig):
    region: str = "us-east-1"
    access_key: str | None = None
    secret_key: str | None = None
    session_token: str | None = None

    @model_validator(mode="after")
    def validate_static_credentials(self) -> "BedrockHTTPClientConfig":
        has_key = self.access_key is not None
        has_secret = self.secret_key is not None
        if has_key != has_secret:
            raise ValueError(
                "Bedrock config requires both access_key and secret_key, or neither. "
                "Provide both for static credentials, or omit both to use IRSA."
            )
        return self
