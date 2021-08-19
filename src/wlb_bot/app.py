import datetime

from aiogram import Bot, Dispatcher, types
from envparse import env
from gcsa.google_calendar import GoogleCalendar
from google.oauth2 import service_account


def auth_to_gcal():
    gc = GoogleCalendar(
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
    events = list(
        gc.get_events(
            time_min=datetime.date(2021, 8, 19),
            time_max=datetime.date(2021, 8, 19),
        )
    )
    events


async def start(message: types.Message):
    await message.answer("Registering your gcal")


def build_bot() -> Dispatcher:
    bot = Bot(token=env.str("WLB_BOT_API_TOKEN"))
    dp = Dispatcher(bot=bot)

    dp.register_message_handler(start, commands=("start",))
    return dp
