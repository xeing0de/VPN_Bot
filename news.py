import asyncio

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import Message

async def forward_news(message: Message, WHITELIST) -> None:
    if not WHITELIST:
        return

    bot = message.bot
    from_chat_id = message.chat.id
    message_id = message.message_id

    for user_id in WHITELIST:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
            except (TelegramBadRequest, TelegramForbiddenError):
                continue
        except (TelegramBadRequest, TelegramForbiddenError):
            continue
