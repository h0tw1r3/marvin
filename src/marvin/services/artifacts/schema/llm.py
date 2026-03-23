from pydantic import BaseModel

from marvin.services.artifacts.schema.base import BaseArtifactSchema, ArtifactType
from marvin.services.cost.schema import CostReportSchema


class LLMArtifactDataSchema(BaseModel):
    prompt: str
    response: str
    cost_report: CostReportSchema | None = None
    prompt_system: str


class LLMArtifactSchema(BaseArtifactSchema[LLMArtifactDataSchema]):
    type: ArtifactType = ArtifactType.LLM
