from aiogram.types import Message

from usermessage import on_any_message, only_whitelist
from userdenied import denied
from news import forward_news

async def chat_choose(message: Message, DATA, INFO, WHITELIST):
    if message.chat.type == "private":
        if await only_whitelist(message, WHITELIST):
            return await on_any_message(message, DATA, INFO)
        return await denied(message)

    chat_id = message.chat.id
    thread_id = message.message_thread_id
    thread_key = f"{chat_id}_{thread_id}"

    name = INFO["allowed_chats"][thread_key]["name"]
    
    if name == "Новости":
        return await forward_news(message, WHITELIST)
    else:
        text = "Чат разрешен, но сценарий ответа не настроен."
        await message.answer(text)
