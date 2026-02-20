import os
import asyncio
import qrcode

from io import BytesIO
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.types import BufferedInputFile
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from data import get_data


TOKEN = os.getenv("TOKEN")
DATA_PATH = "data.json"
DATA = get_data(DATA_PATH)
WHITELIST = {user["id"] for user in DATA["users"]}
USER_BY_ID = {user["id"]: user for user in DATA["users"]}

def main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Доступ к VPN")
    kb.button(text="Информация")
    return kb.as_markup(resize_keyboard=True)

async def only_whitelist(message: Message) -> bool:
    user = message.from_user
    return bool(user and user.id in WHITELIST)

async def denied(message: Message) -> None:
    await message.answer("Доступ запрещён")

def make_qr_png_bytes(data: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def build_vpn_link(user_id: int) -> str:
    template = DATA["template"]
    server = DATA["server"]
    user = USER_BY_ID[user_id]

    profile_name = user.get("name", f"user_{user_id}")
    short_id = user.get("sid", "")

    return template.format(
        uuid=server["uuid"],
        server_ip=server["server_ip"],
        public_key=server["public_key"],
        server_name=server["server_name"],
        short_id=short_id,
        profile_name=profile_name,
    )

async def on_any_message(message: Message) -> None:
    text = (message.text or "").strip()

    if text == "Доступ к VPN":
        user = message.from_user
        link = build_vpn_link(user.id)

        png_bytes = make_qr_png_bytes(link)
        photo = BufferedInputFile(png_bytes, filename="vpn_qr.png")

        await message.answer_photo(photo=photo,caption=link)
        return

    if text == "Информация":
        await message.answer("В разработке...", reply_markup=main_keyboard())
        return

    await message.answer("Выбери кнопку:", reply_markup=main_keyboard())


async def main() -> None:
    bot = Bot(TOKEN)
    dp = Dispatcher()

    dp.message.register(on_any_message, F.text, only_whitelist)
    dp.message.register(denied, F.text)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
