import datetime
import re

from typing import Iterable, Optional, Tuple

import pendulum

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from envparse import env
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account
from pendulum import DateTime


CALENDAR_KEY = "calendar"
UNDERWORK_EVENT_KEY = env.str("WLB_UNDERWORK_EVENT_NAME")
OVERWORK_EVENT_KEY = env.str("WLB_OVERWORK_EVENT_NAME")
WEEK_DETAILS_KEYS = tuple(
    re.compile(key) for key in env.list("WLB_WEEK_DETAILS_KEYS")
)


async def get_gcal(message: types.Message) -> GoogleCalendar:
    try:
        return message.bot[CALENDAR_KEY]
    except KeyError:
        await message.answer("Bot has not been started. Type: /start first.")


def auth_to_gcal() -> GoogleCalendar:
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
    keyboard_markup.row(types.KeyboardButton("/week-details"))
    await message.answer(
        "Welcome to work life balance bot!",
        reply_markup=keyboard_markup,
    )


async def get_weekly_data(message: types.Message):
    gc = await get_gcal(message)
    today = pendulum.now()
    underwork, overwork = await get_balance(today, gc)

    text = f"Week {today.start_of('week').to_date_string()} - {today.end_of('week').to_date_string()}:\n"
    await message.answer(
        (text + "Overworked: " + str(overwork - underwork))
        if overwork >= underwork
        else (text + "Underworked: " + str(underwork - overwork)),
    )


async def get_end_of_working_day(message: types.Message):
    gc = await get_gcal(message)
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


async def render_report(events: Iterable[Event]) -> str:
    """Create a report from gc Events.

      The report looks like:
      ```
      --- 2021-09-17 ---
       start
        07:00:00  07:00:00
       underwork
        15:00:00  15:00:00
       overwork
        15:00:00  15:00:00
    ```
    """
    res = ""
    current_date: Optional[datetime.date] = None
    for event in sorted(events, key=lambda event: event.start):
        if event.start.date() != current_date:
            res += f"\n\n --- {event.start.date()} ---\n"
            current_date = event.start.date()
        res += f"\t{event.summary}\n\t\t{event.start.time()}\t\t{event.end.time()}\n"
    return res


async def get_week_details(message: types.Message):
    gc = await get_gcal(message)
    today = pendulum.now()
    week_events = tuple(
        gc.get_events(
            time_min=today.start_of("week"),
            time_max=today.end_of("week"),
            single_events=True,
            order_by="startTime",
        )
    )
    events_to_report = filter(
        lambda event: any(
            key.match(event.summary) for key in WEEK_DETAILS_KEYS
        ),
        week_events,
    )
    await message.answer(
        await render_report(events_to_report),
        parse_mode=ParseMode.MARKDOWN,
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
    dp.register_message_handler(get_week_details, commands=("week-details",))
    return dp
