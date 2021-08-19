from aiogram.utils import executor

from wlb_bot.app import build_bot


if __name__ == "__main__":
    executor.start_polling(build_bot())
