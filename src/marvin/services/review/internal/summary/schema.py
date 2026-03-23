from pydantic import BaseModel, field_validator

from marvin.config import settings


class SummaryCommentSchema(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return (value or "").strip()

    @property
    def body_with_tag(self):
        return f"{self.text}\n\n{settings.review.summary_tag}"
