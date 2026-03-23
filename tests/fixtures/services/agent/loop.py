from typing import Any

import pytest

from marvin.services.agent.loop.schema import AgentLoopResultSchema
from marvin.services.agent.loop.service import AgentLoopService
from marvin.services.agent.loop.types import AgentLoopServiceProtocol
from tests.fixtures.services.agent.tool import FakeAgentToolService
from tests.fixtures.services.llm import FakeLLMClient
from tests.fixtures.services.prompt import FakePromptService


class FakeAgentLoopService(AgentLoopServiceProtocol):
    def __init__(self, responses: dict[str, Any] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self.responses = responses or {}

    async def run(self, prompt: str, prompt_system: str) -> AgentLoopResultSchema:
        self.calls.append(("run", {"prompt": prompt, "prompt_system": prompt_system}))
        if self.responses.get("raise"):
            raise RuntimeError("agent failed")

        return self.responses.get(
            "run",
            AgentLoopResultSchema(
                final_text="AGENT_FINAL",
                stop_reason="final",
            ),
        )


@pytest.fixture
def agent_loop_service(
        fake_llm_client: FakeLLMClient,
        fake_prompt_service: FakePromptService,
        fake_agent_tool_service: FakeAgentToolService,
) -> AgentLoopService:
    return AgentLoopService(
        llm=fake_llm_client,
        prompt=fake_prompt_service,
        agent_tool=fake_agent_tool_service,
    )


@pytest.fixture
def fake_agent_loop_service() -> FakeAgentLoopService:
    return FakeAgentLoopService()
