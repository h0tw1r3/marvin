from pathlib import Path
from typing import Protocol

from marvin.services.artifacts.schema.base import BaseArtifactSchema
from marvin.services.cost.schema import CostReportSchema
from marvin.services.review.internal.inline.schema import InlineCommentSchema
from marvin.services.review.internal.inline_reply.schema import InlineCommentReplySchema
from marvin.services.review.internal.summary.schema import SummaryCommentSchema
from marvin.services.review.internal.summary_reply.schema import SummaryCommentReplySchema


class ArtifactsServiceProtocol(Protocol):

    # ==========================================
    # Low-level writer
    # ==========================================
    async def save(
            self,
            artifact: BaseArtifactSchema,
            artifacts_dir: Path,
            artifacts_enabled: bool,
    ) -> str | None:
        ...

    # ==========================================
    # High-level: LLM
    # ==========================================
    async def save_llm(
            self,
            prompt: str,
            response: str,
            prompt_system: str,
            cost_report: CostReportSchema | None = None,
    ) -> str | None:
        ...

    # ==========================================
    # High-level: VCS Inline Comment
    # ==========================================
    async def save_vcs_inline(self, comment: InlineCommentSchema) -> str | None:
        ...

    # ==========================================
    # High-level: VCS Summary Comment
    # ==========================================
    async def save_vcs_summary(self, comment: SummaryCommentSchema) -> str | None:
        ...

    # ==========================================
    # High-level: VCS Inline Reply
    # ==========================================
    async def save_vcs_inline_reply(self, thread_id: str, reply: InlineCommentReplySchema) -> str | None:
        ...

    # ==========================================
    # High-level: VCS Summary Reply
    # ==========================================
    async def save_vcs_summary_reply(self, thread_id: str, reply: SummaryCommentReplySchema) -> str | None:
        ...
