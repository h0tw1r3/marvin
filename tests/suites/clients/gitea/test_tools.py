import pytest
from httpx import Response, Request

from marvin.clients.gitea.tools import gitea_has_next_page, build_gitea_headers


def make_response(headers: dict) -> Response:
    return Response(
        request=Request("GET", "http://gitea.test"),
        headers=headers,
        status_code=200,
    )


def test_gitea_has_next_page_true():
    resp = make_response({"Link": '<https://gitea.test?page=2>; rel="next"'})
    assert gitea_has_next_page(resp) is True


def test_gitea_has_next_page_false_empty():
    resp = make_response({"Link": ""})
    assert gitea_has_next_page(resp) is False


def test_gitea_has_next_page_false_missing():
    resp = make_response({})
    assert gitea_has_next_page(resp) is False


# ---------------------------------------------------------------------------
# build_gitea_headers
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("gitea_http_client_config")
def test_build_gitea_headers_uses_token_scheme():
    """Gitea always uses the ``token`` scheme for API auth."""
    headers = build_gitea_headers()

    assert headers == {"Authorization": "token fake-token"}
