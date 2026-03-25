from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.token_type import TokenType


class BitbucketServerPipelineConfig(BaseModel):
    project_key: str
    repo_slug: str
    pull_request_id: int


class BitbucketServerHTTPClientConfig(HTTPClientWithTokenConfig):
    api_token_type: TokenType = TokenType.AUTO
