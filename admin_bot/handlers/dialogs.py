from datetime import datetime
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from admin_bot.states import AdminFSM
from db.queries import get_all_users, get_user_messages_paginated, count_user_messages, get_user_by_id

router = Router()
PAGE_SIZE = 10

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def _user_display(u: dict) -> str:
    username = u.get("username")
    return f"@{username}" if username else (u.get("name") or f"id{u['telegram_id']}")


def _users_keyboard(users: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for u in users:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {_user_display(u)}",
                callback_data=f"admin:user:{u['user_id']}:0",
            )
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _dialog_keyboard(user_id: int, offset: int, total: int) -> InlineKeyboardMarkup:
    buttons = []
    if offset + PAGE_SIZE < total:
        buttons.append([InlineKeyboardButton(text="Загрузить ещё ⬆️", callback_data=f"admin:user:{user_id}:{offset + PAGE_SIZE}")])
    buttons.append([InlineKeyboardButton(text="👥 Назад к списку", callback_data="admin:dialogs")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _format_date_ru(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(str(dt_str)[:19])
        return f"{dt.day} {MONTHS_RU[dt.month]} {dt.year}"
    except Exception:
        return str(dt_str)[:10]


def _group_messages_by_day(messages: list[dict], max_text_len: int = 4000) -> tuple[str, bool]:
    lines = []
    current_day = None
    text_len = 0
    all_fit = True

    for m in messages:
        ts = str(m.get("created_at", ""))
        day = ts[:10]

        day_line = None
        if day != current_day:
            current_day = day
            day_line = f"\n\n📅 {_format_date_ru(ts)}"

        role_label = "Пользователь" if m["role"] == "user" else "Бот"
        msg_line = f"{role_label}: {m['content']}"

        estimated_add = (len(day_line) if day_line else 0) + len(msg_line) + 1
        if text_len + estimated_add > max_text_len:
            all_fit = False
            break

        if day_line:
            lines.append(day_line)
            text_len += len(day_line)
        lines.append(msg_line)
        text_len += len(msg_line) + 1

    return "\n".join(lines).strip(), all_fit


@router.callback_query(lambda c: c.data == "admin:dialogs")
async def show_users(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    users = get_all_users()
    await state.set_state(AdminFSM.viewing_dialogs)
    if not users:
        await callback.message.answer(
            "Пока нет пользователей.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
            ]),
        )
        await callback.answer()
        return

    user_links = "\n".join(
        f"• [{_user_display(u)}](tg://user?id={u['telegram_id']})"
        for u in users
    )
    await callback.message.answer(
        f"👥 *Пользователи ({len(users)}):*\n\n{user_links}",
        parse_mode="Markdown",
        reply_markup=_users_keyboard(users),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("admin:user:"))
async def show_user_dialog(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    parts = callback.data.split(":")
    user_id = int(parts[2])
    offset = int(parts[3])

    user = get_user_by_id(user_id)
    total = count_user_messages(user_id)
    messages = get_user_messages_paginated(user_id, offset=offset, limit=PAGE_SIZE)

    display = _user_display(user) if user else f"user_{user_id}"

    if not messages:
        await callback.message.answer("У пользователя нет сообщений.")
        await callback.answer()
        return

    header = f"💬 *Диалог: {display}* (сообщений: {total})\n"
    body, _ = _group_messages_by_day(messages, max_text_len=4000 - len(header))
    text = header + body

    await state.set_state(AdminFSM.viewing_user_dialog)
    try:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=_dialog_keyboard(user_id, offset, total))
    except Exception:
        await callback.message.answer(text, reply_markup=_dialog_keyboard(user_id, offset, total))
    await callback.answer()
