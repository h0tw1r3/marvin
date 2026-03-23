from typing import Protocol

from marvin.clients.azure_openai.schema import AzureOpenAIChatRequestSchema, AzureOpenAIChatResponseSchema


class AzureOpenAIHTTPClientProtocol(Protocol):
    async def chat(self, request: AzureOpenAIChatRequestSchema) -> AzureOpenAIChatResponseSchema:
        ...
