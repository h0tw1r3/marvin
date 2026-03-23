from marvin.clients.azure_openai.client import get_azure_openai_http_client
from marvin.clients.azure_openai.schema import AzureOpenAIMessage, AzureOpenAIChatRequestSchema
from marvin.config import settings
from marvin.services.llm.types import LLMClientProtocol, ChatResultSchema


class AzureOpenAILLMClient(LLMClientProtocol):
    def __init__(self):
        self.http_client = get_azure_openai_http_client()

    async def chat(self, prompt: str, prompt_system: str) -> ChatResultSchema:
        request = AzureOpenAIChatRequestSchema(
            messages=[
                AzureOpenAIMessage(role="system", content=prompt_system),
                AzureOpenAIMessage(role="user", content=prompt),
            ],
            temperature=settings.llm.meta.temperature,
            max_tokens=settings.llm.meta.max_tokens,
        )
        response = await self.http_client.chat(request)
        return ChatResultSchema(
            text=response.first_text,
            total_tokens=response.usage.total_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
