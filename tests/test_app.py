import pytest

from wlb_bot.app import get_end_of_working_day


@pytest.mark.asyncio
async def test_get_end_of_working_day(message):
    """Just run the handler and ensure message was answered."""
    await get_end_of_working_day(message)
    message.answer.assert_awaited_once()
