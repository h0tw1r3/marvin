from typing import Protocol

from marvin.services.agent.loop.schema import AgentLoopResultSchema
from marvin.services.llm.types import LLMClientProtocol
from marvin.services.prompt.types import PromptServiceProtocol


class AgentLoopServiceProtocol(Protocol):
    llm: LLMClientProtocol
    prompt: PromptServiceProtocol

    async def run(self, prompt: str, prompt_system: str) -> AgentLoopResultSchema:
        ...
