import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = os.getenv("TOKEN")

async def start_handler(message: Message) -> None:
    await message.answer("Привет! Я самый простой бот.")


async def help_handler(message: Message) -> None:
    await message.answer("Доступные команды: /start, /help, /ping")


async def ping_handler(message: Message) -> None:
    await message.answer("pong")


async def echo_handler(message: Message) -> None:
    await message.answer(f"Ты написал: {message.text}")


async def main() -> None:
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(ping_handler, Command("ping"))
    dp.message.register(echo_handler)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
