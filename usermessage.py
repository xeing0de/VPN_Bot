import qrcode
import random
from datetime import datetime, UTC
from uuid import uuid4

from io import BytesIO

from aiogram.types import CallbackQuery
from aiogram.types import BufferedInputFile
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from data import save_data

INFO_PATH = "info.json"
PAYMENT_CALLBACK_PREFIX = "payok:"
DEFAULT_PAYMENT_AMOUNT = 100

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

async def on_any_message(message: Message, DATA, INFO) -> None:
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

    if text == "Оплата":
        payment_channel = find_payment_channel(INFO)
        employee_name, employee = pick_employee_with_lowest_balance(INFO)
        
        amount = int(INFO.get("payment_amount", DEFAULT_PAYMENT_AMOUNT))
        code = f"{random.randint(1000, 9999)}"
        payment_id = uuid4().hex[:12]

        pending = INFO.setdefault("pending_payments", {})
        pending[payment_id] = {
            "status": "pending",
            "user_id": message.from_user.id,
            "employee_name": employee_name,
            "employee_username": employee.get("username", ""),
            "card_number": str(employee.get("number", "")),
            "amount": amount,
            "code": code,
            "created_at": datetime.now(UTC).isoformat(),
        }
        save_data(INFO_PATH, INFO)

        card_number = str(employee.get("number", ""))
        await message.answer(
            "Переведите сумму и укажите код в комментарии к переводу.\n"
            f"Сумма: <b>{amount}</b>\n"
            f"Карта: <code>{card_number}</code>\n"
            f"Код комментария: <code>{code}</code>",
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Подтвердить получение",
                        callback_data=f"{PAYMENT_CALLBACK_PREFIX}{payment_id}",
                    )
                ]
            ]
        )
        chat_id, thread_id = payment_channel
        await message.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=(
                "Новая заявка на оплату\n"
                f"Сотрудник: {employee.get('username')}\n"
                f"Карта: <code>{card_number}</code>\n"
                f"Сумма: <b>{amount}</b>\n"
                f"Код для проверки: <code>{code}</code>\n"
                "Подтвердите после поступления с этим кодом."
            ),
            parse_mode="HTML",
            reply_markup=kb,
        )
        return
    await message.answer("Выбери кнопку:", reply_markup=main_keyboard())

async def on_payment_confirm(callback: CallbackQuery, INFO) -> None:
    raw = callback.data or ""
    if not raw.startswith(PAYMENT_CALLBACK_PREFIX):
        return

    payment_id = raw.removeprefix(PAYMENT_CALLBACK_PREFIX)
    pending = INFO.setdefault("pending_payments", {})
    payment = pending.get(payment_id)
    if not payment:
        await callback.answer("Заявка не найдена или уже обработана.", show_alert=True)
        return

    employee_username = normalize_username(payment.get("employee_username", ""))
    sender_username = normalize_username(callback.from_user.username or "")
    if not employee_username or sender_username != employee_username:
        await callback.answer("Подтверждать может только назначенный сотрудник.", show_alert=True)
        return

    if payment.get("status") != "pending":
        await callback.answer("Эта заявка уже подтверждена.", show_alert=True)
        return

    amount = int(payment.get("amount", 0))
    employee_name = payment.get("employee_name")
    cards = INFO.setdefault("cards", {})
    if employee_name not in cards:
        await callback.answer("Карта сотрудника не найдена.", show_alert=True)
        return

    cards[employee_name]["balance"] = int(cards[employee_name].get("balance", 0)) + amount
    INFO["balance"] = int(INFO.get("balance", 0)) + amount

    payment["status"] = "confirmed"
    payment["confirmed_by"] = callback.from_user.id
    payment["confirmed_at"] = datetime.now(UTC).isoformat()
    save_data(INFO_PATH, INFO)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.answer("Оплата подтверждена.")

    user_id = payment.get("user_id")
    if user_id:
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=(
                    "Ваш перевод подтвержден сотрудником.\n"
                    "Спасибо."
                ),
                parse_mode="HTML",
            )
        except Exception:
            pass

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

def pick_employee_with_lowest_balance(info: dict):
    cards = info.get("cards", {})
    if not cards:
        raise ValueError("В info.json нет cards")
    return min(cards.items(), key=lambda item: int(item[1].get("balance", 0)))

def find_payment_channel(info: dict):
    allowed_chats = info.get("allowed_chats", {})
    for key, payload in allowed_chats.items():
        if payload.get("name") == "Прием оплаты":
            chat_id_str, thread_id_str = key.rsplit("_", 1)
            return int(chat_id_str), int(thread_id_str)
    return None

def normalize_username(value: str) -> str:
    username = value.strip().lstrip("@")
    return username.lower()
