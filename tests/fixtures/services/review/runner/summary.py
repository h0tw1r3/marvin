import pytest

from marvin.services.cost.types import CostServiceProtocol
from marvin.services.diff.types import DiffServiceProtocol
from marvin.services.git.types import GitServiceProtocol
from marvin.services.policy.types import PolicyServiceProtocol
from marvin.services.prompt.types import PromptServiceProtocol
from marvin.services.review.gateway.types import ReviewCommentGatewayProtocol, ReviewLLMGatewayProtocol
from marvin.services.review.internal.summary.types import SummaryCommentServiceProtocol
from marvin.services.review.runner.summary import SummaryReviewRunner
from marvin.services.review.runner.types import ReviewRunnerProtocol
from marvin.services.vcs.types import VCSClientProtocol


class FakeSummaryReviewRunner(ReviewRunnerProtocol):
    def __init__(self):
        self.calls = []

    async def run(self) -> None:
        self.calls.append(("run", {}))


@pytest.fixture
def fake_summary_review_runner() -> FakeSummaryReviewRunner:
    return FakeSummaryReviewRunner()


@pytest.fixture
def summary_review_runner(
        fake_vcs_client: VCSClientProtocol,
        fake_git_service: GitServiceProtocol,
        fake_diff_service: DiffServiceProtocol,
        fake_cost_service: CostServiceProtocol,
        fake_prompt_service: PromptServiceProtocol,
        fake_policy_service: PolicyServiceProtocol,
        fake_review_llm_gateway: ReviewLLMGatewayProtocol,
        fake_review_comment_gateway: ReviewCommentGatewayProtocol,
        fake_summary_comment_service: SummaryCommentServiceProtocol,
) -> SummaryReviewRunner:
    return SummaryReviewRunner(
        vcs=fake_vcs_client,
        git=fake_git_service,
        diff=fake_diff_service,
        cost=fake_cost_service,
        prompt=fake_prompt_service,
        policy=fake_policy_service,
        summary_comment=fake_summary_comment_service,
        review_llm_gateway=fake_review_llm_gateway,
        review_comment_gateway=fake_review_comment_gateway,
    )
