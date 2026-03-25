from httpx import Response

from marvin.config import settings


def gitea_has_next_page(response: Response) -> bool:
    link_header = response.headers.get("Link")
    return link_header is not None and 'rel="next"' in link_header


def build_gitea_headers() -> dict[str, str]:
    """Build the Authorization header for Gitea requests.

    Gitea uses the ``token`` scheme for API authentication.  Basic auth
    is only used to generate API tokens, not for direct API calls.
    """
    return {"Authorization": f"token {settings.vcs.http_client.api_token_value}"}
