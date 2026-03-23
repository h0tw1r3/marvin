from typing import Protocol

from marvin.clients.openai.v2.schema import (
    OpenAIResponsesRequestSchema,
    OpenAIResponsesResponseSchema
)


class OpenAIV2HTTPClientProtocol(Protocol):
    async def chat(self, request: OpenAIResponsesRequestSchema) -> OpenAIResponsesResponseSchema:
        ...
