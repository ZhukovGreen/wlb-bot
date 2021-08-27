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


def auth_to_gcal():
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
    keyboard_markup = types.ReplyKeyboardMarkup()
    keyboard_markup.row(types.KeyboardButton("/week-data"))
    keyboard_markup.row(types.KeyboardButton("/when-go-home"))
    await message.answer(
        "Welcome to work life balance bot!",
        reply_markup=keyboard_markup,
    )


async def get_weekly_data(message: types.Message):
    try:
        gc: GoogleCalendar = message.bot[CALENDAR_KEY]
    except KeyError:
        await message.answer("Bot has not been started. Type: /start first.")
    else:
        today = pendulum.now()
        underwork, overwork = await get_balance(today, gc)

        text = f"Week {today.start_of('week').to_date_string()} - {today.end_of('week').to_date_string()}:\n"
        await message.answer(
            (text + "Overworked: " + str(overwork - underwork))
            if overwork >= underwork
            else (text + "Underworked: " + str(underwork - overwork)),
        )


async def get_end_of_working_day(message: types.Message):
    try:
        gc: GoogleCalendar = message.bot[CALENDAR_KEY]
    except KeyError:
        await message.answer("Bot has not been started. Type: /start first.")
    else:
        today = pendulum.now()
        day_events = tuple(
            gc.get_events(
                time_min=today.start_of("day"),
                time_max=today.end_of("day"),
                single_events=True,
                order_by="startTime",
            )
        )
        *_, last_underwork = filter(is_underwork_event, day_events)
        *_, last_overwork = filter(is_overwork_event, day_events)
        if get_event_length(last_overwork) == datetime.timedelta(0):
            leave_event = last_underwork.start
        else:
            leave_event = last_overwork.end
        await message.answer(
            f"Go home scheduled on {leave_event.hour}:{leave_event.minute}"
        )


def build_dispatcher() -> Dispatcher:
    """Build bot and dispatcher."""
    bot = Bot(token=env.str("WLB_BOT_API_TOKEN"))
    dp = Dispatcher(bot=bot)

    bot[CALENDAR_KEY] = auth_to_gcal()

    dp.register_message_handler(start, commands=("start",))
    dp.register_message_handler(get_weekly_data, commands=("week-data",))
    dp.register_message_handler(
        get_end_of_working_day, commands=("when-go-home",)
    )
    return dp
