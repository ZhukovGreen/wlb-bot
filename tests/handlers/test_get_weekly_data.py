from datetime import timedelta
from unittest.mock import Mock

import pendulum
import pytest

from pendulum import DateTime

from tests.conftest import E
from wlb_bot.app import (
    OVERWORK_EVENT_KEY,
    UNDERWORK_EVENT_KEY,
    auth_to_gcal,
    get_balance,
    get_weekly_data,
)


@pytest.mark.asyncio
async def test_get_weekly_data(message, gcal_get_events_returns, monkeypatch):
    """Ensure over/underworked reported properly.

    As main functionality rely on get_balance, we can test just that it is
    rendering good answers.
    """
    gcal_get_events_returns(())
    monkeypatch.setattr(
        pendulum, "now", Mock(return_value=DateTime(1900, 12, 31))
    )
    await get_weekly_data(message)
    message.answer.assert_awaited_once_with(
        "Week 1900-12-31 - 1901-01-06:\nOverworked: 0:00:00"
    )


@pytest.mark.parametrize(
    ("events", "expected"),
    (
        (
            (
                E(
                    summary=UNDERWORK_EVENT_KEY,
                    start=DateTime(1900, 12, 31, 1),
                    end=DateTime(1900, 12, 31, 2),
                ),
                E(
                    summary=OVERWORK_EVENT_KEY,
                    start=DateTime(1900, 12, 31, 1),
                    end=DateTime(1900, 12, 31, 2),
                ),
            ),
            (
                timedelta(seconds=3600),
                timedelta(seconds=3600),
            ),
        ),
        (
            (
                E(
                    summary="not UNDERWORK_EVENT_KEY",
                    start=DateTime(1900, 12, 31, 1),
                    end=DateTime(1900, 12, 31, 2),
                ),
                E(
                    summary="not OVERWORK_EVENT_KEY",
                    start=DateTime(1900, 12, 31, 1),
                    end=DateTime(1900, 12, 31, 2),
                ),
            ),
            (
                timedelta(0),
                timedelta(0),
            ),
        ),
        (
            (),
            (
                timedelta(0),
                timedelta(0),
            ),
        ),
    ),
)
@pytest.mark.asyncio
async def test_get_balance(gcal_get_events_returns, events, expected):
    """Test over/under work balance calculated properly.

    With various inputs from the calendar.
    """
    gcal_get_events_returns(events)
    assert await get_balance(DateTime.today(), auth_to_gcal()) == expected
