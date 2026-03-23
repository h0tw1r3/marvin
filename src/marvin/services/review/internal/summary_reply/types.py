from typing import Protocol

from marvin.services.review.internal.summary_reply.schema import SummaryCommentReplySchema


class SummaryCommentReplyServiceProtocol(Protocol):
    def parse_model_output(self, output: str) -> SummaryCommentReplySchema:
        ...
