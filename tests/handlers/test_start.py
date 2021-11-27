import pytest

from aiogram.types import ReplyKeyboardMarkup

from wlb_bot.app import start


@pytest.mark.asyncio
async def test_start_keyboard_markup_created(message):
    """Ensure KeyboardMarkup was created."""
    await start(message)
    assert isinstance(
        message.answer.call_args.kwargs["reply_markup"], ReplyKeyboardMarkup
    )


@pytest.mark.asyncio
async def test_start_answer_sent(message):
    """Ensure answer was sent."""
    await start(message)
    assert isinstance(message.answer.call_args.args[0], str)
