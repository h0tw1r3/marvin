from datetime import datetime, UTC
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4


class ArtifactType(StrEnum):
    LLM = "LLM_INTERACTION"
    VCS_INLINE = "VCS_INLINE"
    VCS_SUMMARY = "VCS_SUMMARY"
    VCS_INLINE_REPLY = "VCS_INLINE_REPLY"
    VCS_SUMMARY_REPLY = "VCS_SUMMARY_REPLY"


class BaseArtifactSchema[ArtifactData: BaseModel](BaseModel):
    id: UUID4 = Field(default_factory=uuid4)
    type: ArtifactType
    data: ArtifactData
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
