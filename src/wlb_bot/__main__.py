from aiogram.utils import executor

from wlb_bot.app import build_dispatcher


if __name__ == "__main__":
    executor.start_polling(build_dispatcher())
