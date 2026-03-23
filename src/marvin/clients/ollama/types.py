from typing import Protocol

from marvin.clients.ollama.schema import OllamaChatRequestSchema, OllamaChatResponseSchema


class OllamaHTTPClientProtocol(Protocol):
    async def chat(self, request: OllamaChatRequestSchema) -> OllamaChatResponseSchema:
        ...
