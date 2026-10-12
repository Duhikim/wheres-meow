import pytest

from integration_support import AppEnv, build_app_env


@pytest.fixture
def app_env() -> AppEnv:
    return build_app_env()
