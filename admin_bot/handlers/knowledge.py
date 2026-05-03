import os
import tempfile
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, Document
from admin_bot.states import AdminFSM
from ai.rag import list_sources, delete_by_source
from knowledge.indexer import index_file

logger = logging.getLogger(__name__)
router = Router()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _knowledge_keyboard(has_docs: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📤 Загрузить документ", callback_data="kb:upload")],
    ]
    if has_docs:
        buttons.append([InlineKeyboardButton(text="Удалить", callback_data="kb:delete_ask")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _format_sources_list(sources: list[dict]) -> str:
    lines = ["📚 База знаний:\n"]
    for i, src in enumerate(sources, 1):
        name = src["source"]
        lines.append(f"{i}. {name}")
    return "\n".join(lines)


@router.callback_query(lambda c: c.data == "admin:knowledge")
async def show_knowledge(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.knowledge_menu)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    sources = list_sources()
    await state.update_data(kb_sources=sources)
    if sources:
        text = _format_sources_list(sources)
        await callback.message.answer(
            text,
            reply_markup=_knowledge_keyboard(has_docs=True),
        )
    else:
        await callback.message.answer(
            "📚 База знаний пуста.\nЗагрузи первый документ:",
            reply_markup=_knowledge_keyboard(has_docs=False),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "kb:upload")
async def ask_for_document(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.waiting_document)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "📤 Отправь файл для загрузки в базу знаний.\n"
        "Поддерживаемые форматы: *PDF, TXT, DOCX*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin:knowledge")],
        ]),
    )
    await callback.answer()


@router.message(AdminFSM.waiting_document, F.document)
async def receive_document(message: Message, state: FSMContext) -> None:
    doc: Document = message.document
    file_name = doc.file_name or "document"
    ext = os.path.splitext(file_name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        await message.answer(
            f"❌ Формат {ext} не поддерживается. Загрузи PDF, TXT или DOCX.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 База знаний", callback_data="admin:knowledge")],
            ]),
        )
        return

    await message.answer(f"⏳ Обрабатываю файл *{file_name}*...", parse_mode="Markdown")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        file = await message.bot.get_file(doc.file_id)
        await message.bot.download_file(file.file_path, tmp_path)
        index_file(tmp_path, source_name=file_name)
        await state.set_state(AdminFSM.knowledge_menu)
        await message.answer(
            f"✅ Загружен файл: *{file_name}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 База знаний", callback_data="admin:knowledge")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
            ]),
        )
    except Exception as exc:
        logger.error("Failed to index %s: %s", file_name, exc)
        await message.answer(
            f"❌ Ошибка при индексировании: {exc}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📚 База знаний", callback_data="admin:knowledge")],
            ]),
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.callback_query(lambda c: c.data == "kb:delete_ask")
async def ask_delete_number(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.waiting_delete_number)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(
        "Введите номер документа который хотите удалить из базы знаний:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin:knowledge")],
        ]),
    )
    await callback.answer()


@router.message(AdminFSM.waiting_delete_number, F.text)
async def receive_delete_number(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Введите только цифру — номер документа из списка.")
        return

    data = await state.get_data()
    sources = data.get("kb_sources") or list_sources()
    index = int(text) - 1

    if index < 0 or index >= len(sources):
        await message.answer(
            f"Документ с номером {text} не найден. Введите корректный номер.",
        )
        return

    source_name = sources[index]["source"]
    delete_by_source(source_name)
    await state.set_state(AdminFSM.knowledge_menu)
    await message.answer(
        f"✅ Документ *{source_name}* удалён.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 База знаний", callback_data="admin:knowledge")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")],
        ]),
    )
