import pytest

import wlb_bot

from wlb_bot.app import CALENDAR_KEY, auth_to_gcal, get_weekly_data


def test_basic():
    auth_to_gcal()


@pytest.mark.asyncio
async def test_get_weekly_data(monkeypatch):
    monkeypatch.setattr(
        wlb_bot.app.types.Message, "bot", {CALENDAR_KEY: auth_to_gcal()}
    )
    await get_weekly_data(None)
