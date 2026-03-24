import os
from enum import StrEnum


class ConfigError(Exception):
    """Raised for config file loading, parsing, or interpolation failures."""


class ConfigEnv(StrEnum):
    ENV = "MARVIN_CONFIG_FILE_ENV"
    YAML = "MARVIN_CONFIG_FILE_YAML"
    JSON = "MARVIN_CONFIG_FILE_JSON"


def get_config_file_or_default(variable: str, default_filename: str) -> str:
    return os.getenv(variable, os.path.join(os.getcwd(), default_filename))


def get_env_config_file_or_default() -> str:
    return get_config_file_or_default(ConfigEnv.ENV, ".env")


def get_yaml_config_file_or_default() -> str:
    return get_config_file_or_default(ConfigEnv.YAML, ".marvin.yaml")


def get_json_config_file_or_default() -> str:
    return get_config_file_or_default(ConfigEnv.JSON, ".marvin.json")
