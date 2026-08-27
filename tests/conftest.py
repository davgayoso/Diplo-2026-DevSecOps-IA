from dataclasses import replace

import pytest

from app.config import Settings, settings


@pytest.fixture
def secure_settings() -> Settings:
    return replace(
        settings,
        reader_api_key="reader-test-key-1234567890",
        admin_api_key="admin-test-key-1234567890",
        rate_limit_requests=10,
        rate_limit_window_seconds=60,
    )
