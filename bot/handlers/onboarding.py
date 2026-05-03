from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.states import UserFSM
from db.queries import get_or_create_user, get_user_by_telegram_id
from datetime import datetime
from pathlib import Path

router = Router()

CONSENT_TEXT = (
    "👋 Привет! Я - Трансформатор жизни, твой персональный коуч по личным границам.\n\n"
    "Нажимая «Начать» - ты соглашаешься с обработкой персональных данных - "
    "ID профиля, имя и история сообщений для обеспечения работы бота."
)

WELCOME_NEW = (
    "👋 Привет! Я — *Трансформатор жизни*, твой коуч по личным границам.\n\n"
    "Я помогаю разобраться в сложных ситуациях, понять свои чувства и найти путь "
    "к себе. Я не заменяю психолога, но всегда рядом, чтобы поддержать тебя.\n\n"
    "Что будем делать?"
)

WELCOME_BACK = "С возвращением! Опиши свою ситуацию или улучши навыки через тренажёр."

MAIN_MENU_TEXT = (
    "Привет. Я тренажёр личных границ и взрослой коммуникации.\n\n"
    "Пришли мне ситуацию из жизни:\n"
    "- что тебе сказали\n"
    "- что произошло\n"
    "- что ты ответил (если ответил)\n"
    "- что тебя задело\n\n"
    "И я помогу тебе разобраться и стать сильнее в таких моментах."
)


def consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data="consent:agree")]
    ])


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Описать ситуацию", callback_data="mode:situation")]
    ])


def _save_consent(username: str | None) -> None:
    login = username or "unknown"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    consent_file = Path("/opt/transformation-bot/data/consents/consents.txt")
    consent_file.parent.mkdir(parents=True, exist_ok=True)
    with open(consent_file, "a", encoding="utf-8") as f:
        f.write(f"{login},{timestamp}\n")


async def _clear_last_keyboard(bot, chat_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    msg_id = data.get("last_kbd_msg_id")
    if msg_id:
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        except Exception:
            pass


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    name = message.from_user.first_name or message.from_user.username or "друг"

    await _clear_last_keyboard(message.bot, message.chat.id, state)

    # Проверяем в БД: пользователь уже зарегистрирован?
    user_in_db = get_user_by_telegram_id(telegram_id)
    if user_in_db:
        # Пользователь уже есть в БД — пропускаем согласие, идём в меню
        await state.set_state(UserFSM.choosing_mode)
        sent = await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
        await state.update_data(last_kbd_msg_id=sent.message_id)
    else:
        # Новый пользователь — показываем согласие
        get_or_create_user(telegram_id, name, message.from_user.username)
        await state.set_state(UserFSM.consent)
        await state.update_data(temp_username=message.from_user.username)
        sent = await message.answer(CONSENT_TEXT, reply_markup=consent_keyboard())
        await state.update_data(last_kbd_msg_id=sent.message_id)


@router.callback_query(lambda c: c.data == "consent:agree")
async def consent_agree(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    username = data.get("temp_username")
    _save_consent(username)

    await state.set_state(UserFSM.choosing_mode)
    try:
        await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    except Exception:
        pass
    await state.update_data(last_kbd_msg_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:main")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserFSM.choosing_mode)
    try:
        await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    except Exception:
        pass
    await state.update_data(last_kbd_msg_id=callback.message.message_id)
    await callback.answer()


@router.message(UserFSM.choosing_mode, F.text)
async def choosing_mode_text(message: Message, state: FSMContext) -> None:
    await _clear_last_keyboard(message.bot, message.chat.id, state)
    sent = await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    await state.update_data(last_kbd_msg_id=sent.message_id)
