import pytest

from pendulum import DateTime

from tests.conftest import E
from wlb_bot.app import (
    OVERWORK_EVENT_KEY,
    UNDERWORK_EVENT_KEY,
    get_end_of_working_day,
)


@pytest.mark.parametrize(
    ("events", "answer"),
    (
        (
            (
                E(
                    summary="start",
                    start=DateTime(1900, 12, 31),
                    end=DateTime(1900, 12, 31),
                ),
            ),
            "No data for today.",
        ),
        (
            (
                E(
                    summary=UNDERWORK_EVENT_KEY,
                    start=DateTime(1900, 12, 31),
                    end=DateTime(1900, 12, 31),
                ),
                E(
                    summary=OVERWORK_EVENT_KEY,
                    start=DateTime(1900, 12, 31),
                    end=DateTime(1900, 12, 31),
                ),
            ),
            "Go home scheduled on 00:00:00",
        ),
    ),
)
@pytest.mark.asyncio
async def test_get_end_of_working_day(
    message,
    gcal_get_events_returns,
    events,
    answer,
):
    """Just run the handler and ensure message was answered."""
    gcal_get_events_returns(events)
    await get_end_of_working_day(message)
    message.answer.assert_awaited_once_with(answer)
