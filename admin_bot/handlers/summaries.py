from datetime import datetime
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from admin_bot.states import AdminFSM
from db.queries import get_users_with_summaries, get_user_by_id, get_summary

router = Router()


def _user_display(u: dict) -> str:
    username = u.get("username")
    return f"@{username}" if username else (u.get("name") or f"id{u['telegram_id']}")


def _summaries_keyboard(users: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for u in users:
        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {_user_display(u)}",
                callback_data=f"summary:show:{u['user_id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔄 Обновить сводки", callback_data="summary:refresh")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _summaries_keyboard_empty() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить сводки", callback_data="summary:refresh")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
    ])


@router.callback_query(lambda c: c.data == "admin:summaries")
async def show_summaries(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.viewing_summaries)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    users = get_users_with_summaries()
    if not users:
        await callback.message.answer(
            "📋 Сводок пока нет. Нажмите «Обновить сводки» для генерации.",
            reply_markup=_summaries_keyboard_empty(),
        )
        await callback.answer()
        return

    user_links = "\n".join(
        f"• [{_user_display(u)}](tg://user?id={u['telegram_id']})"
        for u in users
    )
    await callback.message.answer(
        f"📋 *Сводки пользователей ({len(users)}):*\n\n{user_links}",
        parse_mode="Markdown",
        reply_markup=_summaries_keyboard(users),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("summary:show:"))
async def show_user_summary(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    user_id = int(callback.data.split(":")[2])
    user = get_user_by_id(user_id)
    summary = get_summary(user_id)

    display = _user_display(user) if user else f"user_{user_id}"
    text = f"📋 *Сводка: {display}*\n\n{summary or 'Сводка отсутствует.'}"

    try:
        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Назад к сводкам", callback_data="admin:summaries")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
            ]),
        )
    except Exception:
        await callback.message.answer(
            f"Сводка: {display}\n\n{summary or 'Сводка отсутствует.'}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Назад к сводкам", callback_data="admin:summaries")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
            ]),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "summary:refresh")
async def refresh_summaries(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer("⏳ Обновляю сводки...")
    await callback.answer()

    from scheduler.daily_job import run_full_refresh
    count = await run_full_refresh()

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await callback.message.answer(f"✅ Сводки обновлены. Актуальны на {now}")

    users = get_users_with_summaries()
    if not users:
        await callback.message.answer(
            "📋 Сводок пока нет — не хватает истории диалогов.",
            reply_markup=_summaries_keyboard_empty(),
        )
        return

    user_links = "\n".join(
        f"• [{_user_display(u)}](tg://user?id={u['telegram_id']})"
        for u in users
    )
    await callback.message.answer(
        f"📋 *Сводки пользователей ({len(users)}):*\n\n{user_links}",
        parse_mode="Markdown",
        reply_markup=_summaries_keyboard(users),
    )
