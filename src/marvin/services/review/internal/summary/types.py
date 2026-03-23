from typing import Protocol

from marvin.services.review.internal.summary.schema import SummaryCommentSchema


class SummaryCommentServiceProtocol(Protocol):
    def parse_model_output(self, output: str) -> SummaryCommentSchema:
        ...
