import re

import pytest

from pendulum import DateTime

from tests.conftest import E
from wlb_bot import app
from wlb_bot.app import get_week_details


@pytest.mark.parametrize(
    ("events", "expected"),
    (
        (
            (
                E(
                    summary="good_start_summary",
                    start=DateTime(1900, 12, 31),
                    end=DateTime(1900, 12, 31),
                ),
            ),
            "\n\n --- 1900-12-31 ---\n\tgood_start_summary\n\t\t00:00:00\t\t00:00:00\n",
        ),
        (
            (
                E(
                    summary="bad_start_summary",
                    start=DateTime(1900, 12, 31),
                    end=DateTime(1900, 12, 31),
                ),
            ),
            "",
        ),
        (
            (),
            "",
        ),
    ),
)
@pytest.mark.asyncio
async def test_get_week_details(
    message,
    gcal_get_events_returns,
    monkeypatch,
    events,
    expected,
):
    """Just run the handler and ensure message was answered."""
    gcal_get_events_returns(events)
    monkeypatch.setattr(app, "WEEK_DETAILS_KEYS", (re.compile("^good_start"),))

    await get_week_details(message)
    message.answer.assert_awaited_once_with(expected)
