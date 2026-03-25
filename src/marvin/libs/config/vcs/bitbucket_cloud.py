from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig
from marvin.libs.config.token_type import TokenType


class BitbucketCloudPipelineConfig(BaseModel):
    workspace: str
    repo_slug: str
    pull_request_id: str


class BitbucketCloudHTTPClientConfig(HTTPClientWithTokenConfig):
    api_token_type: TokenType = TokenType.AUTO
