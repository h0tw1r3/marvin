from httpx import Response

from marvin.config import settings
from marvin.libs.http.authentication import build_authorization_header


def gitlab_has_next_page(response: Response) -> bool:
    return bool(response.headers.get("X-Next-Page"))


def build_gitlab_headers() -> dict[str, str]:
    """Build the Authorization header for GitLab requests."""
    return build_authorization_header(
        settings.vcs.http_client.api_token_type,
        settings.vcs.http_client.api_token_value,
    )
