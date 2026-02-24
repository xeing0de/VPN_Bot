import os
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from data import get_data, get_info
from choose import chat_choose

TOKEN = os.getenv("TOKEN")
DATA_PATH = "data.json"
INFO_PATH = "info.json"
DATA = get_data(DATA_PATH)
INFO = get_info(INFO_PATH)
WHITELIST = {
    int(user_id) for user_id, payload in DATA["users"].items()
    if payload["time"] > 0
}

async def only_allowed_chats(message: Message, INFO) -> bool:
    if message.chat.type == "private":
        return True
    allowed_raw = INFO.get("allowed_chats", {})
    allowed = {k for k in allowed_raw.keys()}

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    return f"{chat_id}_{thread_id}" in allowed

async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp["DATA"] = DATA
    dp["WHITELIST"] = WHITELIST
    dp["INFO"] = INFO

    dp.message.register(chat_choose, F.text, only_allowed_chats)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
