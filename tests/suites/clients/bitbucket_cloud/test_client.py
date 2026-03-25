import httpx
import pytest
from httpx import AsyncClient

from marvin.clients.bitbucket_cloud.client import get_bitbucket_cloud_http_client, BitbucketCloudHTTPClient
from marvin.clients.bitbucket_cloud.pr.client import (
    BitbucketCloudPullRequestsHTTPClient,
    BitbucketCloudPullRequestsHTTPClientError,
)


@pytest.mark.usefixtures("bitbucket_cloud_http_client_config")
def test_get_bitbucket_cloud_http_client_builds_ok():
    bitbucket_http_client = get_bitbucket_cloud_http_client()

    assert isinstance(bitbucket_http_client, BitbucketCloudHTTPClient)
    assert isinstance(bitbucket_http_client.pr, BitbucketCloudPullRequestsHTTPClient)
    assert isinstance(bitbucket_http_client.pr.client, AsyncClient)


@pytest.mark.asyncio
async def test_delete_comment_sends_delete_to_comment_resource():
    requests_made: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_made.append((request.method, str(request.url)))
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)
    async with AsyncClient(transport=transport, base_url="https://api.bitbucket.org/2.0") as ac:
        client = BitbucketCloudPullRequestsHTTPClient(ac)
        await client.delete_comment("myws", "myrepo", "42", "7")

    assert len(requests_made) == 1
    assert requests_made[0][0] == "DELETE"
    assert "/repositories/myws/myrepo/pullrequests/42/comments/7" in requests_made[0][1]


@pytest.mark.asyncio
async def test_delete_comment_treats_404_as_idempotent_success():
    transport = httpx.MockTransport(lambda _request: httpx.Response(404))
    async with AsyncClient(transport=transport, base_url="https://api.bitbucket.org/2.0") as ac:
        client = BitbucketCloudPullRequestsHTTPClient(ac)
        await client.delete_comment("w", "r", "1", "99")


@pytest.mark.asyncio
async def test_delete_comment_raises_on_non_404_error():
    transport = httpx.MockTransport(lambda _request: httpx.Response(403, text="forbidden"))

    async with AsyncClient(transport=transport, base_url="https://api.bitbucket.org/2.0") as ac:
        client = BitbucketCloudPullRequestsHTTPClient(ac)
        with pytest.raises(BitbucketCloudPullRequestsHTTPClientError) as exc_info:
            await client.delete_comment("w", "r", "1", "99")

    assert exc_info.value.status_code == 403
