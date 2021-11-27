import typing

from unittest.mock import AsyncMock, Mock

import attr
import pytest

from aiogram import Bot
from aiogram.types import Message
from gcsa.google_calendar import GoogleCalendar
from gcsa.serializers.event_serializer import EventSerializer
from pendulum import DateTime

from wlb_bot.app import build_dispatcher


@pytest.fixture()
def bot(monkeypatch):
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


sample_event = {
    "kind": "calendar#event",
    "etag": '"3263124324234000"',
    "id": "_FDGsdfhiufwniKHKJNKHIDFDJFLKDMVKEFVFNVEjknvsdfsdhifsjjkJKHkjnkjhkjhk050000Z",
    "status": "confirmed",
    "htmlLink": "https://www.google.com/calendar/event?eid=RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR5azZzcTNhYmExOGNvNDhiYTI2a3MzZWRxMTY4cTNhaDlrNjhfMjAyMTA5MTNUMDUwMDAwWiBlNW9nczlyNTRvN2IxZG45ZmcyajFpYjhoZ0Bn",
    "created": "2021-08-09T05:59:29.000Z",
    "updated": "2021-09-14T04:42:41.528Z",
    "summary": "start",
    "creator": {"email": "iam@zhukovgreen.pro"},
    "organizer": {
        "email": "dddddddddddddddddddddddddd@group.calendar.google.com",
        "displayName": "Planned routines",
        "self": True,
    },
    "start": {"dateTime": "2021-09-13T06:45:00+02:00"},
    "end": {"dateTime": "2021-09-13T06:45:00+02:00"},
    "recurringEventId": "_23423dfdfdsf3234dgdgr2324234234sfasfdsdf6ks3edq168q3ah9k68",
    "originalStartTime": {"dateTime": "2021-09-13T07:00:00+02:00"},
    "iCalUID": "BBB8B111-11F1-4745-AC0D-B5877A245E43",
    "sequence": 1,
    "reminders": {"useDefault": True},
    "eventType": "default",
}


@attr.dataclass
class E:
    """Simplified version of the GoogleCalendar event."""

    summary: str = attr.ib()
    start: DateTime = attr.ib()
    end: DateTime = attr.ib()

    def as_gcal_event(self):
        """Serialize into GoogleCalendar event."""
        event = sample_event.copy()
        event["summary"] = self.summary
        event["start"]["dateTime"] = self.start.to_iso8601_string()
        event["end"]["dateTime"] = self.end.to_iso8601_string()
        return EventSerializer(event).get_object()


@pytest.fixture()
def gcal_get_events_returns(
    monkeypatch,
) -> typing.Callable[[typing.Tuple[E, ...]], None]:
    """A factory for patching the get_events method of the GoogleCalendar.

    Example:
    >>> def test_example(
    >>>     gcal_get_events_returns,
    >>> ):
    >>>     gcal_get_events_returns((E("a", DateTime(...), DateTime(...)),))
    >>>     # at this moment GoogleCalendar.get_events will return these events
    """

    def factory(events: typing.Tuple[E, ...]):
        monkeypatch.setattr(
            GoogleCalendar,
            "get_events",
            Mock(return_value=(e.as_gcal_event() for e in events)),
        )

    return factory
