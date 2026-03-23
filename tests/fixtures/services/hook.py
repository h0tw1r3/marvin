import pytest

from marvin.services.hook import HookService


@pytest.fixture
def hook_service() -> HookService:
    return HookService()
