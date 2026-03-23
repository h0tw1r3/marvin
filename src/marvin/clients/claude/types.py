from typing import Protocol

from marvin.clients.claude.schema import ClaudeChatRequestSchema, ClaudeChatResponseSchema


class ClaudeHTTPClientProtocol(Protocol):
    async def chat(self, request: ClaudeChatRequestSchema) -> ClaudeChatResponseSchema:
        ...
