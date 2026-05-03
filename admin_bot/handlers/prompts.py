import asyncio
import yaml
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from admin_bot.states import AdminFSM
from config import SITUATION_PROMPT_PATH, TRAINER_EVAL_PROMPT_PATH, SUMMARY_PROMPT_PATH

router = Router()

_user_locks: dict[int, asyncio.Lock] = {}


def _get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in _user_locks:
        _user_locks[user_id] = asyncio.Lock()
    return _user_locks[user_id]

PROMPT_FILES = {
    "situation": SITUATION_PROMPT_PATH,
    "trainer_eval": TRAINER_EVAL_PROMPT_PATH,
    "summary": SUMMARY_PROMPT_PATH,
}

PROMPT_LABELS = {
    "situation": "💬 Ситуация",
    "trainer_eval": "🏋️ Тренажёр ответов",
    "summary": "📋 Сводка",
}


def _prompts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ситуация", callback_data="prompt:show:situation")],
        [InlineKeyboardButton(text="🏋️ Тренажёр ответов", callback_data="prompt:show:trainer_eval")],
        [InlineKeyboardButton(text="📋 Сводка", callback_data="prompt:show:summary")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
    ])


def _read_prompt(key: str) -> str:
    path = PROMPT_FILES[key]
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("system_prompt", "") or ""


def _write_prompt(key: str, new_text: str) -> None:
    path = PROMPT_FILES[key]
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({"system_prompt": new_text}, f, allow_unicode=True, default_flow_style=False)


@router.callback_query(lambda c: c.data == "admin:prompts")
async def show_prompts_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.main_menu)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "✏️ *Редактирование промтов*\n\nВыберите промт:",
        parse_mode="Markdown",
        reply_markup=_prompts_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("prompt:show:"))
async def show_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    key = callback.data.split(":")[2]
    content = _read_prompt(key)
    label = PROMPT_LABELS.get(key, key)

    await state.update_data(editing_prompt_key=key)
    await state.set_state(AdminFSM.waiting_prompt_text)

    await callback.message.answer(f"📄 *Текущий промт — {label}:*", parse_mode="Markdown")

    if content.strip():
        chunk_size = 3900
        for i in range(0, len(content), chunk_size):
            await callback.message.answer(f"```\n{content[i:i+chunk_size]}\n```", parse_mode="Markdown")
    else:
        await callback.message.answer("_Промт пуст._", parse_mode="Markdown")

    await state.update_data(prompt_parts=[], last_part_msg_id=None)
    await callback.message.answer(
        "Отправь новый текст промта — можно несколькими сообщениями подряд.\n"
        "После последней части появится кнопка *Сохранить*.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад к промтам", callback_data="admin:prompts")],
        ]),
    )
    await callback.answer()


@router.message(AdminFSM.waiting_prompt_text, F.text)
async def receive_new_prompt(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    data = await state.get_data()
    key = data.get("editing_prompt_key")

    if text.lower() == "/cancel":
        await state.set_state(AdminFSM.main_menu)
        await message.answer("Отменено.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
        ]))
        return

    if not key:
        await message.answer("Ошибка: не выбран промт. Начни сначала.")
        return

    lock = _get_user_lock(message.from_user.id)
    async with lock:
        data = await state.get_data()
        parts = data.get("prompt_parts", [])
        last_part_msg_id = data.get("last_part_msg_id")

        if last_part_msg_id:
            try:
                await message.bot.delete_message(message.chat.id, last_part_msg_id)
            except Exception:
                pass

        parts.append(text)
        total = sum(len(p) for p in parts)

        if len(parts) == 1:
            status_text = f"📨 Часть 1 получена ({total} симв.).\nОтправь следующую часть или нажми *Сохранить*."
        else:
            status_text = f"📨 Получено частей: {len(parts)}, итого {total} симв.\nОтправь следующую часть или нажми *Сохранить*."

        sent = await message.answer(
            status_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💾 Сохранить", callback_data="prompt:save")],
                [InlineKeyboardButton(text="↩️ Отмена", callback_data="admin:prompts")],
            ]),
        )
        await state.update_data(prompt_parts=parts, last_part_msg_id=sent.message_id)


@router.callback_query(lambda c: c.data == "prompt:save")
async def save_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("editing_prompt_key")
    parts = data.get("prompt_parts", [])

    if not parts:
        await callback.answer("Нет текста для сохранения.", show_alert=True)
        return
    if not key:
        await callback.answer("Ошибка: не выбран промт.", show_alert=True)
        return

    full_text = "".join(parts)
    _write_prompt(key, full_text)
    label = PROMPT_LABELS.get(key, key)
    await state.set_state(AdminFSM.main_menu)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer(
        f"✅ Промт *{label}* обновлён.\n"
        f"Частей: {len(parts)}, символов: {len(full_text)}.\n"
        f"Бот применит изменения при следующем запросе пользователя.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Промты", callback_data="admin:prompts")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
        ]),
    )
    await callback.answer()
