import json
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    SettingsConfigDict,
    PydanticBaseSettingsSource
)

from marvin.libs.config.agent import AgentConfig
from marvin.libs.config.artifacts import ArtifactsConfig
from marvin.libs.config.base import (
    ConfigError,
    get_env_config_file_or_default,
    get_yaml_config_file_or_default,
    get_json_config_file_or_default
)
from marvin.libs.config.core import CoreConfig
from marvin.libs.config.interpolation import expand_env_in_structure
from marvin.libs.config.llm.base import LLMConfig
from marvin.libs.config.logger import LoggerConfig
from marvin.libs.config.prompt import PromptConfig
from marvin.libs.config.review import ReviewConfig
from marvin.libs.config.vcs.base import VCSConfig


def _load_file(path: Path, parser: str) -> dict[str, Any]:
    """Read and parse a config file, returning an empty dict if it doesn't exist.

    Raises :class:`ConfigError` for invalid content or non-mapping root types.
    """
    if not path.is_file():
        return {}

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read config file {path}: {exc}") from exc

    try:
        if parser == "yaml":
            raw = yaml.safe_load(text)
        else:
            raw = json.loads(text) if text.strip() else None
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Invalid {parser.upper()} in {path}: {exc}") from exc

    if raw is None:
        return {}

    if not isinstance(raw, dict):
        raise ConfigError(
            f"Top-level config must be a mapping, "
            f"got {type(raw).__name__}: {path}"
        )

    return raw


class InterpolatingYamlSettingsSource(InitSettingsSource):
    """Loads YAML config with Docker Compose–style ``${VAR}`` interpolation."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        path = Path(get_yaml_config_file_or_default())
        raw = _load_file(path, "yaml")
        expanded = expand_env_in_structure(raw)
        super().__init__(settings_cls, expanded)


class InterpolatingJsonSettingsSource(InitSettingsSource):
    """Loads JSON config with Docker Compose–style ``${VAR}`` interpolation."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        path = Path(get_json_config_file_or_default())
        raw = _load_file(path, "json")
        expanded = expand_env_in_structure(raw)
        super().__init__(settings_cls, expanded)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra='allow',

        env_file=get_env_config_file_or_default(),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    llm: LLMConfig
    vcs: VCSConfig
    core: CoreConfig = CoreConfig()
    agent: AgentConfig = AgentConfig()
    prompt: PromptConfig = PromptConfig()
    review: ReviewConfig = ReviewConfig()
    logger: LoggerConfig = LoggerConfig()
    artifacts: ArtifactsConfig = ArtifactsConfig()

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            InterpolatingYamlSettingsSource(cls),
            InterpolatingJsonSettingsSource(cls),
            env_settings,
            dotenv_settings,
            init_settings,
        )


settings = Settings()
