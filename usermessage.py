import qrcode

from io import BytesIO

from aiogram.types import BufferedInputFile
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder

#WHITELIST
async def only_whitelist(message: Message, WHITELIST) -> bool:
    user = message.from_user
    return bool(user and user.id in WHITELIST)

#ANSWER
def main_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Доступ к VPN")
    kb.button(text="Информация")
    kb.button(text="Помощь")
    kb.button(text="Оплата")
    return kb.as_markup(resize_keyboard=True)

async def on_any_message(message: Message, DATA) -> None:
    text = (message.text or "").strip()

    if text == "Доступ к VPN":
        user = message.from_user
        link = build_vpn_link(user.id, DATA)

        png_bytes = make_qr_png_bytes(link)
        photo = BufferedInputFile(png_bytes, filename="vpn_qr.png")
        
        await message.answer("QR-Code и ссылка")
        await message.answer_photo(photo=photo,caption=link)
        return

    if text == "Информация":
        user = message.from_user
        user_id = user.id
        user_data = DATA["users"].get(str(user_id))

        profile_name = user_data.get("name", f"user_{user_id}")
        time = user_data.get("time", "—")

        info_text = (
            "<b>Информация о пользователе</b>\n"
            "────────────────────────\n"
            f"ID: <code>{user_id}</code>\n"
            f"Имя: {profile_name}\n"
            f"Остаток: {time}\n"
            "────────────────────────\n"
        )

        await message.answer(info_text, reply_markup=main_keyboard(), parse_mode="HTML")
        return

    await message.answer("Выбери кнопку:", reply_markup=main_keyboard())

#LINK AND QR
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

def build_vpn_link(user_id: int, DATA) -> str:
    template = DATA["template"]
    server = DATA["server"]
    user = DATA["users"][str(user_id)]

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
