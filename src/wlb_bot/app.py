import datetime

from typing import Tuple

import pendulum

from aiogram import Bot, Dispatcher, types
from envparse import env
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account
from pendulum import DateTime


CALENDAR_KEY = "calendar"
UNDERWORK_EVENT_KEY = env.str("WLB_UNDERWORK_EVENT_NAME")
OVERWORK_EVENT_KEY = env.str("WLB_OVERWORK_EVENT_NAME")


async def auth_to_gcal():
    """Create GoogleCalendar instance."""
    return GoogleCalendar(
        calendar=env.str("WLB_CALENDAR_ID"),
        credentials=service_account.Credentials.from_service_account_info(
            {
                "type": env.str("WLB_TYPE"),
                "project_id": env.str("WLB_PROJECT_ID"),
                "private_key_id": env.str("WLB_PRIVATE_KEY_ID"),
                "private_key": env.str("WLB_PRIVATE_KEY"),
                "client_email": env.str("WLB_CLIENT_EMAIL"),
                "client_id": env.str("WLB_CLIENT_ID"),
                "auth_uri": env.str("WLB_AUTH_URI"),
                "token_uri": env.str("WLB_TOKEN_URI"),
                "auth_provider_x509_cert_url": env.str(
                    "WLB_AUTH_PROVIDER_X509_CERT_URL"
                ),
                "client_x509_cert_url": env.str("WLB_CLIENT_X509_CERT_URL"),
            }
        ),
    )


async def get_balance(
    today: DateTime,
    gc: GoogleCalendar,
) -> Tuple[datetime.timedelta, datetime.timedelta]:
    """Get timedelta balances of underwork and overwork.

    Function sums all events length named $WLB_OVERWORK_EVENT_NAME and $WLB_UNDERWORK_EVENT_NAME and
    returns the result in a form of sum timedelta.

    The timeframe where events are queried is the week start and week end based on today date.
    """
    events = tuple(
        gc.get_events(
            time_min=today.start_of("week"),
            time_max=today.end_of("week"),
            single_events=True,
            order_by="startTime",
        )
    )

    underwork = sum(
        map(
            get_event_length,
            filter(is_underwork_event, events),
        ),
        datetime.timedelta(),
    )
    overwork = sum(
        map(
            get_event_length,
            filter(is_overwork_event, events),
        ),
        datetime.timedelta(),
    )
    return underwork, overwork


def is_overwork_event(event: Event) -> bool:
    return event.summary == OVERWORK_EVENT_KEY


def is_underwork_event(event: Event) -> bool:
    return event.summary == UNDERWORK_EVENT_KEY


def get_event_length(event: Event) -> datetime.timedelta:
    return event.end - event.start


async def start(message: types.Message):
    """Start command handler.

    If user is admin, then the command authenticate the google calendar.
    """
    if message.from_user.username == env.str("WLB_ADMIN_USERNAME"):
        message.bot[CALENDAR_KEY] = await auth_to_gcal()
        keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
        keyboard_markup.row(types.KeyboardButton("/week-data"))
        await message.answer(
            "Google calendar authenticated.",
            reply_markup=keyboard_markup,
        )
    else:
        await message.answer("You are not authenticated to start this bot")


async def get_weekly_data(message: types.Message):
    try:
        gc: GoogleCalendar = message.bot[CALENDAR_KEY]
    except KeyError:
        await message.answer("Bot has not been started. Type: /start first.")
    else:
        today = pendulum.now()
        underwork, overwork = await get_balance(today, gc)

        await message.answer(
            f"Week {today.start_of('week').to_date_string()} - {today.end_of('week').to_date_string()}:\n"
            + ("Overworked: " + str(overwork - underwork))
            if overwork >= underwork
            else ("Underworked: " + str(underwork - overwork)),
        )


def build_bot() -> Dispatcher:
    """Build bot and dispatcher."""
    bot = Bot(token=env.str("WLB_BOT_API_TOKEN"))
    dp = Dispatcher(bot=bot)

    dp.register_message_handler(start, commands=("start",))
    dp.register_message_handler(get_weekly_data, commands=("week-data",))
    return dp
