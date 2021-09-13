import pytest

from wlb_bot.app import get_end_of_working_day, get_week_details


@pytest.mark.asyncio
async def test_get_end_of_working_day(message):
    """Just run the handler and ensure message was answered."""
    await get_end_of_working_day(message)
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_weekdetails(message):
    """Just run the handler and ensure message was answered."""
    await get_week_details(message)
    message.answer.assert_awaited_once()
