import pendulum

from aiogram import Bot, Dispatcher, types
from envparse import env
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account


CALENDAR_KEY = "calendar"


def auth_to_gcal():
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


async def start(message: types.Message):
    message.bot[CALENDAR_KEY] = auth_to_gcal()
    await message.answer("Registering your gcal")


async def get_weekly_data(message: types.Message):
    gc: GoogleCalendar = message.bot[CALENDAR_KEY]
    today = pendulum.now()
    start_of_week = today.start_of("week")
    end_of_week = today.end_of("week")
    await message.answer(
        "\n".join(
            repr(event)
            for event in gc.get_events(
                time_min=start_of_week, time_max=end_of_week
            )
        )
    )


def build_bot() -> Dispatcher:
    bot = Bot(token=env.str("WLB_BOT_API_TOKEN"))
    dp = Dispatcher(bot=bot)

    dp.register_message_handler(start, commands=("start",))
    dp.register_message_handler(get_weekly_data, commands=("week-data",))
    return dp
