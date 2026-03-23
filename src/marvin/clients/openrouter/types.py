from typing import Protocol

from marvin.clients.openrouter.schema import (
    OpenRouterChatRequestSchema,
    OpenRouterChatResponseSchema
)


class OpenRouterHTTPClientProtocol(Protocol):
    async def chat(self, request: OpenRouterChatRequestSchema) -> OpenRouterChatResponseSchema:
        ...
