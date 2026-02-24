from aiogram.types import Message

async def denied(message: Message) -> None:
    await message.answer("Доступ запрещён")



