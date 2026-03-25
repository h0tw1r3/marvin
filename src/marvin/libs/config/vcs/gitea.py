from pydantic import BaseModel

from marvin.libs.config.http import HTTPClientWithTokenConfig


class GiteaPipelineConfig(BaseModel):
    repo: str
    owner: str
    pull_number: str


class GiteaHTTPClientConfig(HTTPClientWithTokenConfig):
    """Gitea HTTP client config.

    Gitea uses the ``token`` auth scheme for all API calls. Basic auth
    is only supported for generating API tokens, not for direct API
    calls, so there is no ``api_token_type`` field here.
    """
