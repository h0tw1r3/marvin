from typing import Protocol

from marvin.clients.gemini.schema import GeminiChatRequestSchema, GeminiChatResponseSchema


class GeminiHTTPClientProtocol(Protocol):
    async def chat(self, request: GeminiChatRequestSchema) -> GeminiChatResponseSchema:
        ...
