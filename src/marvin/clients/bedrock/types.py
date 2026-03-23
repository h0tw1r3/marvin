from typing import Protocol

from marvin.clients.bedrock.schema import BedrockChatRequestSchema, BedrockChatResponseSchema


class BedrockHTTPClientProtocol(Protocol):
    async def chat(self, request: BedrockChatRequestSchema) -> BedrockChatResponseSchema:
        ...
