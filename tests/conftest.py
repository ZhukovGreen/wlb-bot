from unittest.mock import AsyncMock

import pytest

from aiogram import Bot
from aiogram.types import Message

from wlb_bot.app import build_dispatcher


@pytest.fixture()
def bot():
    """Fixture which returns the Bot instance."""
    return build_dispatcher().bot


@pytest.fixture()
def message(bot) -> "MessageMock":  # type: ignore # noqa: F821
    """Message fixture with embedded bot"""

    class MessageMock(Message):
        """Mock object used instead of Message.

        Plug the bot fixture as a property and modify answer method to just emit the log.
        """

        @property
        def bot(self) -> Bot:
            """Get bot instance."""
            return bot

        answer: AsyncMock = AsyncMock()

    return MessageMock()
