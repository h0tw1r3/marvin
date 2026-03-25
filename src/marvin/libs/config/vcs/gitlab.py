from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.token_type import TokenType


class GitLabPipelineConfig(BaseModel):
    project_id: str
    merge_request_id: str


class GitLabHTTPClientConfig(HTTPClientWithTokenConfig):
    api_token_type: TokenType = TokenType.AUTO
