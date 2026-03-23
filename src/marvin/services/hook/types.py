from collections.abc import Callable, Awaitable

from marvin.services.cost.schema import CostReportSchema
from marvin.services.review.internal.inline.schema import InlineCommentSchema
from marvin.services.review.internal.inline_reply.schema import InlineCommentReplySchema
from marvin.services.review.internal.summary.schema import SummaryCommentSchema
from marvin.services.review.internal.summary_reply.schema import SummaryCommentReplySchema
from marvin.services.vcs.types import ReviewCommentSchema

HookFunc = Callable[..., Awaitable[None]]

ChatStartHookFunc = Callable[[str, str], Awaitable[None]]
ChatErrorHookFunc = Callable[[str, str], Awaitable[None]]
ChatCompleteHookFunc = Callable[[str, CostReportSchema | None], Awaitable[None]]

InlineReviewStartHookFunc = Callable[..., Awaitable[None]]
InlineReviewCompleteHookFunc = Callable[[CostReportSchema | None], Awaitable[None]]

ContextReviewStartHookFunc = Callable[..., Awaitable[None]]
ContextReviewCompleteHookFunc = Callable[[CostReportSchema | None], Awaitable[None]]

SummaryReviewStartHookFunc = Callable[..., Awaitable[None]]
SummaryReviewCompleteHookFunc = Callable[[CostReportSchema | None], Awaitable[None]]

InlineReplyReviewStartHookFunc = Callable[..., Awaitable[None]]
InlineReplyReviewCompleteHookFunc = Callable[[CostReportSchema | None], Awaitable[None]]

SummaryReplyReviewStartHookFunc = Callable[..., Awaitable[None]]
SummaryReplyReviewCompleteHookFunc = Callable[[CostReportSchema | None], Awaitable[None]]

InlineCommentStartHookFunc = Callable[[InlineCommentSchema], Awaitable[None]]
InlineCommentErrorHookFunc = Callable[[InlineCommentSchema], Awaitable[None]]
InlineCommentCompleteHookFunc = Callable[[InlineCommentSchema], Awaitable[None]]

SummaryCommentStartHookFunc = Callable[[SummaryCommentSchema], Awaitable[None]]
SummaryCommentErrorHookFunc = Callable[[SummaryCommentSchema], Awaitable[None]]
SummaryCommentCompleteHookFunc = Callable[[SummaryCommentSchema], Awaitable[None]]

InlineCommentReplyStartHookFunc = Callable[[InlineCommentReplySchema], Awaitable[None]]
InlineCommentReplyErrorHookFunc = Callable[[InlineCommentReplySchema], Awaitable[None]]
InlineCommentReplyCompleteHookFunc = Callable[[InlineCommentReplySchema], Awaitable[None]]

SummaryCommentReplyStartHookFunc = Callable[[SummaryCommentReplySchema], Awaitable[None]]
SummaryCommentReplyErrorHookFunc = Callable[[SummaryCommentReplySchema], Awaitable[None]]
SummaryCommentReplyCompleteHookFunc = Callable[[SummaryCommentReplySchema], Awaitable[None]]

ClearInlineCommentsStartHookFunc = Callable[..., Awaitable[None]]
ClearInlineCommentsErrorHookFunc = Callable[..., Awaitable[None]]
ClearInlineCommentsCompleteHookFunc = Callable[[list[ReviewCommentSchema]], Awaitable[None]]

ClearSummaryCommentsStartHookFunc = Callable[..., Awaitable[None]]
ClearSummaryCommentsErrorHookFunc = Callable[..., Awaitable[None]]
ClearSummaryCommentsCompleteHookFunc = Callable[[list[ReviewCommentSchema]], Awaitable[None]]
