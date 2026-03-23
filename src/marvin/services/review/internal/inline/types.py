from typing import Protocol

from marvin.services.review.internal.inline.schema import InlineCommentListSchema


class InlineCommentServiceProtocol(Protocol):
    def parse_model_output(self, output: str) -> InlineCommentListSchema:
        ...
