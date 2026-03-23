from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig


class GitHubPipelineConfig(BaseModel):
    repo: str
    owner: str
    pull_number: str


class GitHubHTTPClientConfig(HTTPClientWithTokenConfig):
    pass
