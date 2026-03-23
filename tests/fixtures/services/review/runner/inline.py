import pytest

from marvin.services.cost.types import CostServiceProtocol
from marvin.services.diff.types import DiffServiceProtocol
from marvin.services.git.types import GitServiceProtocol
from marvin.services.policy.types import PolicyServiceProtocol
from marvin.services.prompt.types import PromptServiceProtocol
from marvin.services.review.gateway.types import ReviewLLMGatewayProtocol, ReviewCommentGatewayProtocol
from marvin.services.review.internal.inline.types import InlineCommentServiceProtocol
from marvin.services.review.runner.inline import InlineReviewRunner
from marvin.services.review.runner.types import ReviewRunnerProtocol
from marvin.services.vcs.types import VCSClientProtocol


class FakeInlineReviewRunner(ReviewRunnerProtocol):
    def __init__(self):
        self.calls = []

    async def run(self) -> None:
        self.calls.append(("run", {}))


@pytest.fixture
def fake_inline_review_runner() -> FakeInlineReviewRunner:
    return FakeInlineReviewRunner()


@pytest.fixture
def inline_review_runner(
        fake_vcs_client: VCSClientProtocol,
        fake_git_service: GitServiceProtocol,
        fake_diff_service: DiffServiceProtocol,
        fake_cost_service: CostServiceProtocol,
        fake_prompt_service: PromptServiceProtocol,
        fake_policy_service: PolicyServiceProtocol,
        fake_review_llm_gateway: ReviewLLMGatewayProtocol,
        fake_review_comment_gateway: ReviewCommentGatewayProtocol,
        fake_inline_comment_service: InlineCommentServiceProtocol,
) -> InlineReviewRunner:
    return InlineReviewRunner(
        vcs=fake_vcs_client,
        git=fake_git_service,
        diff=fake_diff_service,
        cost=fake_cost_service,
        prompt=fake_prompt_service,
        policy=fake_policy_service,
        inline_comment=fake_inline_comment_service,
        review_llm_gateway=fake_review_llm_gateway,
        review_comment_gateway=fake_review_comment_gateway,
    )
