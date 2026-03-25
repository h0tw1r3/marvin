from enum import StrEnum

from pydantic import BaseModel, DirectoryPath, field_validator, Field


class ArtifactFormat(StrEnum):
    """On-disk serialization for saved artifacts (debug/audit dumps)."""

    JSON = "json"
    YAML = "yaml"


class ArtifactsConfig(BaseModel):
    llm_dir: DirectoryPath = Field(default=DirectoryPath("./artifacts/llm"), validate_default=True)
    vcs_dir: DirectoryPath = Field(default=DirectoryPath("./artifacts/vcs"), validate_default=True)
    llm_enabled: bool = False
    vcs_enabled: bool = False
    format: ArtifactFormat = Field(
        default=ArtifactFormat.YAML,
        description=(
            "Artifact serialization mode. "
            "json is lossless and best for machine processing; "
            "yaml is display-oriented and may sanitize control characters "
            "(not byte-faithful)."
        ),
    )

    @field_validator('llm_dir', 'vcs_dir', mode='before')
    @classmethod
    def validate_directories(cls, value: DirectoryPath | str) -> DirectoryPath:
        directory = DirectoryPath(value)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
