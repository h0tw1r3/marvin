from marvin.libs.config.http import HTTPClientConfig
from marvin.libs.config.llm.meta import LLMMetaConfig


class OllamaMetaConfig(LLMMetaConfig):
    stop: list[str] | None = None
    seed: int | None = None
    model: str = "llama2"
    top_p: float | None = None
    num_ctx: int | None = None
    repeat_penalty: float | None = None


class OllamaHTTPClientConfig(HTTPClientConfig):
    pass
