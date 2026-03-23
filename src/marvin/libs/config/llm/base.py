from functools import cached_property
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, FilePath

from marvin.libs.config.llm.azure_openai import AzureOpenAIHTTPClientConfig, AzureOpenAIMetaConfig
from marvin.libs.config.llm.bedrock import BedrockHTTPClientConfig, BedrockMetaConfig
from marvin.libs.config.llm.claude import ClaudeHTTPClientConfig, ClaudeMetaConfig
from marvin.libs.config.llm.gemini import GeminiHTTPClientConfig, GeminiMetaConfig
from marvin.libs.config.llm.ollama import OllamaHTTPClientConfig, OllamaMetaConfig
from marvin.libs.config.llm.openai import OpenAIHTTPClientConfig, OpenAIMetaConfig
from marvin.libs.config.llm.openrouter import OpenRouterHTTPClientConfig, OpenRouterMetaConfig
from marvin.libs.constants.llm_provider import LLMProvider
from marvin.libs.resources import load_resource


class LLMPricingConfig(BaseModel):
    input: float
    output: float


class LLMConfigBase(BaseModel):
    provider: LLMProvider
    pricing_file: FilePath | None = None

    @cached_property
    def pricing_file_or_default(self):
        if self.pricing_file and self.pricing_file.exists():
            return self.pricing_file

        return load_resource(
            package="marvin.resources",
            filename="pricing.yaml",
            fallback="src/marvin/resources/pricing.yaml"
        )

    def load_pricing(self) -> dict[str, LLMPricingConfig]:
        data = self.pricing_file_or_default.read_text(encoding="utf-8")
        raw = yaml.safe_load(data)
        return {model: LLMPricingConfig(**values) for model, values in raw.items()}


class OpenAILLMConfig(LLMConfigBase):
    meta: OpenAIMetaConfig
    provider: Literal[LLMProvider.OPENAI]
    http_client: OpenAIHTTPClientConfig


class GeminiLLMConfig(LLMConfigBase):
    meta: GeminiMetaConfig
    provider: Literal[LLMProvider.GEMINI]
    http_client: GeminiHTTPClientConfig


class ClaudeLLMConfig(LLMConfigBase):
    meta: ClaudeMetaConfig
    provider: Literal[LLMProvider.CLAUDE]
    http_client: ClaudeHTTPClientConfig


class OllamaLLMConfig(LLMConfigBase):
    meta: OllamaMetaConfig
    provider: Literal[LLMProvider.OLLAMA]
    http_client: OllamaHTTPClientConfig


class BedrockLLMConfig(LLMConfigBase):
    meta: BedrockMetaConfig
    provider: Literal[LLMProvider.BEDROCK]
    http_client: BedrockHTTPClientConfig


class OpenRouterLLMConfig(LLMConfigBase):
    meta: OpenRouterMetaConfig
    provider: Literal[LLMProvider.OPENROUTER]
    http_client: OpenRouterHTTPClientConfig


class AzureOpenAILLMConfig(LLMConfigBase):
    meta: AzureOpenAIMetaConfig
    provider: Literal[LLMProvider.AZURE_OPENAI]
    http_client: AzureOpenAIHTTPClientConfig


LLMConfig = Annotated[
    OpenAILLMConfig
    | GeminiLLMConfig
    | ClaudeLLMConfig
    | OllamaLLMConfig
    | BedrockLLMConfig
    | OpenRouterLLMConfig
    | AzureOpenAILLMConfig,
    Field(discriminator="provider")
]
