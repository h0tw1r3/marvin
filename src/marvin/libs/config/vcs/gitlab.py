from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig


class GitLabPipelineConfig(BaseModel):
    project_id: str
    merge_request_id: str


class GitLabHTTPClientConfig(HTTPClientWithTokenConfig):
    pass
