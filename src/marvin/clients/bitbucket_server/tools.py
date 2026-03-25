from httpx import Response

from marvin.config import settings
from marvin.libs.http.authentication import build_authorization_header


def bitbucket_server_has_next_page(response: Response) -> bool:
    data = response.json()
    return not data.get("isLastPage", True)


def build_bitbucket_server_headers() -> dict[str, str]:
    """Build the Authorization header for Bitbucket Server requests."""
    return build_authorization_header(
        settings.vcs.http_client.api_token_type,
        settings.vcs.http_client.api_token_value,
    )
