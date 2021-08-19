import pytest

from wlb_bot.app import build_bot


@pytest.fixture
def bot():
    dp = build_bot()
    return dp
