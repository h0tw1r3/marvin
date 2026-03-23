from marvin.config import settings
from marvin.libs.constants.llm_provider import LLMProvider
from marvin.services.llm.azure_openai.client import AzureOpenAILLMClient
from marvin.services.llm.bedrock.client import BedrockLLMClient
from marvin.services.llm.claude.client import ClaudeLLMClient
from marvin.services.llm.gemini.client import GeminiLLMClient
from marvin.services.llm.ollama.client import OllamaLLMClient
from marvin.services.llm.openai.client import OpenAILLMClient
from marvin.services.llm.openrouter.client import OpenRouterLLMClient
from marvin.services.llm.types import LLMClientProtocol


def get_llm_client() -> LLMClientProtocol:
    match settings.llm.provider:
        case LLMProvider.OPENAI:
            return OpenAILLMClient()
        case LLMProvider.GEMINI:
            return GeminiLLMClient()
        case LLMProvider.CLAUDE:
            return ClaudeLLMClient()
        case LLMProvider.OLLAMA:
            return OllamaLLMClient()
        case LLMProvider.BEDROCK:
            return BedrockLLMClient()
        case LLMProvider.OPENROUTER:
            return OpenRouterLLMClient()
        case LLMProvider.AZURE_OPENAI:
            return AzureOpenAILLMClient()
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.llm.provider}")
