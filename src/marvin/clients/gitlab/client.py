from httpx import AsyncClient, AsyncHTTPTransport

from marvin.clients.gitlab.mr.client import GitLabMergeRequestsHTTPClient
from marvin.clients.gitlab.tools import build_gitlab_headers
from marvin.config import settings
from marvin.libs.http.event_hooks.logger import LoggerEventHook
from marvin.libs.http.transports.retry import RetryTransport
from marvin.libs.logger import get_logger


class GitLabHTTPClient:
    def __init__(self, client: AsyncClient):
        self.mr = GitLabMergeRequestsHTTPClient(client)


def get_gitlab_http_client() -> GitLabHTTPClient:
    logger = get_logger("GITLAB_HTTP_CLIENT")
    logger_event_hook = LoggerEventHook(logger=logger)
    retry_transport = RetryTransport(
        logger=logger,
        transport=AsyncHTTPTransport(
            proxy=settings.vcs.http_client.proxy_url_value,
            verify=settings.vcs.http_client.verify
        )
    )

    client = AsyncClient(
        verify=settings.vcs.http_client.verify,
        timeout=settings.vcs.http_client.timeout,
        headers=build_gitlab_headers(),
        base_url=settings.vcs.http_client.api_url_value,
        transport=retry_transport,
        event_hooks={
            "request": [logger_event_hook.request],
            "response": [logger_event_hook.response]
        }
    )

    return GitLabHTTPClient(client=client)
