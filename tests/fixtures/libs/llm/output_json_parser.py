import pytest
from pydantic import BaseModel

from marvin.libs.llm.output_json_parser import LLMOutputJSONParser


class DummyModel(BaseModel):
    text: str


@pytest.fixture
def llm_output_json_parser() -> LLMOutputJSONParser:
    return LLMOutputJSONParser(DummyModel)
