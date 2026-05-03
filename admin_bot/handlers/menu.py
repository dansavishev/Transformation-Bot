import httpx
import json
import sys
import shutil
import asyncio
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from admin_bot.states import AdminFSM
from config import OPENROUTER_API_KEY

CHANGELOG_DIR = Path("/opt/transformation-bot/changelog")
PROJECT_DIR = Path("/opt/transformation-bot")

logger = logging.getLogger("admin_bot.menu")
router = Router()


def _load_unpublished() -> list:
    """Читает entries.json и возвращает только записи с published=False."""
    entries_file = CHANGELOG_DIR / "data" / "entries.json"
    if not entries_file.exists():
        return []
    with open(entries_file, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)
    return [e for e in all_entries if not e.get('published', False)]


def _merge_to_changelog(entries: list) -> Path:
    """Мержит записи в changelog.json, возвращает путь к web_dest."""
    changelog_file = CHANGELOG_DIR / "data" / "changelog.json"
    if changelog_file.exists():
        with open(changelog_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    else:
        existing = []
    clean = [{k: v for k, v in e.items() if k != 'published'} for e in entries]
    existing.extend(clean)
    existing.sort(key=lambda x: x.get('date', ''), reverse=True)
    with open(changelog_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    web_dest = Path("/opt/transformation-bot/data/changelog.json")
    web_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(changelog_file, web_dest)

    # Копируем также в changelog-v2.json чтобы избежать кеша GitHub Pages
    web_dest_v2 = Path("/opt/transformation-bot/data/changelog-v2.json")
    shutil.copy2(changelog_file, web_dest_v2)

    # ДОЛГОСРОЧНОЕ РЕШЕНИЕ: автоматический git push
    try:
        subprocess.run(
            ['git', 'add', 'data/changelog.json', 'data/changelog-v2.json'],
            cwd=str(PROJECT_DIR),
            check=True,
            capture_output=True,
            timeout=10
        )
        subprocess.run(
            ['git', 'commit', '-m', f'Publish changelog [{datetime.now().isoformat()}]'],
            cwd=str(PROJECT_DIR),
            check=False,  # не критично если нечего коммитить
            capture_output=True,
            timeout=10
        )
        subprocess.run(
            ['git', 'push', 'origin', 'master'],
            cwd=str(PROJECT_DIR),
            check=True,
            capture_output=True,
            timeout=30
        )
        logger.info("Changelog published to GitHub successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr.decode() if e.stderr else str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during git push: {e}")

    return web_dest


def _changelog_list_keyboard(unpublished: list) -> InlineKeyboardMarkup:
    """Строит клавиатуру со списком записей."""
    buttons = []
    for idx, entry in enumerate(unpublished):
        date = entry.get('date', '?')
        group = entry.get('group', '?')
        buttons.append([InlineKeyboardButton(
            text=f"📅 {date} | {group}",
            callback_data=f"cl:view:{idx}"
        )])
    buttons.append([InlineKeyboardButton(text="✅ Опубликовать всё", callback_data="cl:pub_all")])
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="admin:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _publish_changelog_via_api(local_path: Path, notify_message) -> None:
    """Публикует changelog.json на GitHub через REST API — без git subprocess."""
    import sys
    sys.path.insert(0, str(CHANGELOG_DIR))
    from github_api import push_file_to_github

    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        await notify_message.answer("⚠️ GITHUB_TOKEN не задан в .env")
        return

    loop = asyncio.get_event_loop()
    try:
        success = await loop.run_in_executor(
            None,
            push_file_to_github,
            str(local_path),
            "data/changelog.json",
            token,
            None,
        )
        if success:
            await notify_message.answer("✅ Сайт обновлён — изменения появятся через ~1 минуту")
        else:
            await notify_message.answer("⚠️ Не удалось опубликовать на GitHub, проверь логи")
    except Exception as e:
        logger.error(f"GitHub API ошибка: {e}")
        await notify_message.answer(f"⚠️ Ошибка публикации: {e}")


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Диалоги пользователей", callback_data="admin:dialogs")],
        [InlineKeyboardButton(text="✏️ Редактировать промты", callback_data="admin:prompts")],
        [InlineKeyboardButton(text="📚 База знаний", callback_data="admin:knowledge")],
        [InlineKeyboardButton(text="📋 Сводки пользователей", callback_data="admin:summaries")],
        [InlineKeyboardButton(text="💰 Баланс OpenRouter", callback_data="admin:balance")],
        [InlineKeyboardButton(text="📝 Выложить изменения", callback_data="admin:changelog")],
    ])


@router.message(CommandStart())
async def admin_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminFSM.main_menu)
    await message.answer(
        "🛠 *Панель администратора — Трансформатор жизни*\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(lambda c: c.data == "admin:balance")
async def check_balance(callback: CallbackQuery) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/credits",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            total = float(data.get("total_credits", 0))
            used = float(data.get("total_usage", 0))
            balance = total - used
        await callback.answer()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
        ])
        await callback.message.answer(f"💰 *Баланс OpenRouter:* ${balance:.2f}", parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.answer()
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
        ])
        await callback.message.answer("Не удалось получить баланс", reply_markup=kb)


@router.callback_query(lambda c: c.data == "admin:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFSM.main_menu)
    await callback.message.edit_text(
        "🛠 *Панель администратора — Трансформатор жизни*\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:changelog")
async def publish_changes_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает список неопубликованных записей из entries.json"""
    unpublished = _load_unpublished()

    if not unpublished:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin:main")]
        ])
        await callback.message.answer("📭 Нет неопубликованных изменений", reply_markup=kb)
        await callback.answer()
        return

    await state.update_data(unpublished=unpublished)
    text = f"📋 Неопубликованных записей: {len(unpublished)}\n\nВыбери запись для просмотра или опубликуй всё:"
    await callback.message.answer(text, reply_markup=_changelog_list_keyboard(unpublished))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("cl:view:"))
async def view_changelog_entry(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает конкретную запись с кнопками редактирования и публикации"""
    try:
        idx = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка в номере записи", show_alert=True)
        return

    data = await state.get_data()
    unpublished = data.get('unpublished', [])

    if idx >= len(unpublished):
        await callback.answer("❌ Запись не найдена", show_alert=True)
        return

    entry = unpublished[idx]
    date = entry.get('date', '?')
    group = entry.get('group', '?')
    changes = entry.get('changes', [])

    text = f"📅 {date} | {group}\n\n"
    for ch in changes:
        text += f"• {ch}\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"cl:edit:{idx}"),
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"cl:pub:{idx}"),
        ],
        [InlineKeyboardButton(text="↩️ К списку", callback_data="cl:back")],
    ])
    await state.set_state(AdminFSM.viewing_changelog_entry)
    await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data == "cl:back")
async def back_to_changelog_list(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает к списку записей"""
    unpublished = _load_unpublished()

    if not unpublished:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin:main")]
        ])
        await callback.message.answer("📭 Нет неопубликованных изменений", reply_markup=kb)
        await callback.answer()
        return

    await state.update_data(unpublished=unpublished)
    text = f"📋 Неопубликованных записей: {len(unpublished)}\n\nВыбери запись:"
    await callback.message.answer(text, reply_markup=_changelog_list_keyboard(unpublished))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("cl:edit:"))
async def edit_changelog_entry(callback: CallbackQuery, state: FSMContext) -> None:
    """Переход в режим редактирования конкретной записи"""
    try:
        idx = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка в номере записи", show_alert=True)
        return

    data = await state.get_data()
    unpublished = data.get('unpublished', [])

    if idx >= len(unpublished):
        await callback.answer("❌ Запись не найдена", show_alert=True)
        return

    entry = unpublished[idx]
    template = f"📅 {entry.get('date')} | {entry.get('group')}\n"
    for ch in entry.get('changes', []):
        template += f"• {ch}\n"

    await state.update_data(editing_idx=idx)
    await state.set_state(AdminFSM.editing_changelog)
    await callback.message.answer(
        f"✏️ Отредактируй и отправь обратно:\n\n{template.strip()}"
    )
    await callback.answer()


@router.message(AdminFSM.editing_changelog)
async def process_edited_changelog(message: Message, state: FSMContext) -> None:
    """Обработка отредактированного текста"""
    sys.path.insert(0, str(CHANGELOG_DIR))
    from parser import parse_user_input, validate_parsed

    parsed = parse_user_input(message.text)

    if not parsed or not validate_parsed(parsed):
        await message.answer(
            "❌ Ошибка при парсинге. Проверь формат:\n\n"
            "📅 2026-05-03 | Группа\n"
            "• Изменение"
        )
        return

    data = await state.get_data()
    idx = data.get('editing_idx', 0)
    unpublished = data.get('unpublished', [])

    new_entry = parsed[0]

    entries_file = CHANGELOG_DIR / "data" / "entries.json"
    with open(entries_file, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)

    if idx < len(unpublished):
        orig = unpublished[idx]
        for i, e in enumerate(all_entries):
            if e.get('date') == orig.get('date') and e.get('group') == orig.get('group'):
                all_entries[i] = {**new_entry, 'published': False}
                break

    with open(entries_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    unpublished = [e for e in all_entries if not e.get('published', False)]
    await state.update_data(unpublished=unpublished)

    entry = new_entry
    text = f"✅ Обновлено!\n\n📅 {entry.get('date')} | {entry.get('group')}\n\n"
    for ch in entry.get('changes', []):
        text += f"• {ch}\n"

    new_idx = next(
        (i for i, e in enumerate(unpublished)
         if e.get('date') == entry.get('date') and e.get('group') == entry.get('group')),
        0
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"cl:edit:{new_idx}"),
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"cl:pub:{new_idx}"),
        ],
        [InlineKeyboardButton(text="↩️ К списку", callback_data="cl:back")],
    ])
    await state.set_state(AdminFSM.viewing_changelog_entry)
    await message.answer(text, reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("cl:pub:"))
async def publish_one_entry(callback: CallbackQuery, state: FSMContext) -> None:
    """Публикует одну запись"""
    try:
        idx = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка в номере записи", show_alert=True)
        return

    data = await state.get_data()
    unpublished = data.get('unpublished', [])

    if idx >= len(unpublished):
        await callback.answer("❌ Запись не найдена", show_alert=True)
        return

    entry = unpublished[idx]

    entries_file = CHANGELOG_DIR / "data" / "entries.json"
    with open(entries_file, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)

    for e in all_entries:
        if e.get('date') == entry.get('date') and e.get('group') == entry.get('group'):
            e['published'] = True
            break

    with open(entries_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    web_dest = _merge_to_changelog([entry])

    await callback.message.answer("✅ Опубликовано. Публикую на сайт...")
    await callback.answer()
    asyncio.create_task(_publish_changelog_via_api(web_dest, callback.message))

    remaining = [e for e in all_entries if not e.get('published', False)]
    if remaining:
        await state.update_data(unpublished=remaining)
        await callback.message.answer(
            f"📋 Осталось неопубликованных: {len(remaining)}",
            reply_markup=_changelog_list_keyboard(remaining)
        )
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
        ])
        await callback.message.answer("📭 Все записи опубликованы", reply_markup=kb)


@router.callback_query(lambda c: c.data == "cl:pub_all")
async def publish_all_entries(callback: CallbackQuery, state: FSMContext) -> None:
    """Публикует все неопубликованные записи"""
    data = await state.get_data()
    unpublished = data.get('unpublished', [])

    if not unpublished:
        await callback.answer("❌ Нет записей для публикации", show_alert=True)
        return

    entries_file = CHANGELOG_DIR / "data" / "entries.json"
    with open(entries_file, 'r', encoding='utf-8') as f:
        all_entries = json.load(f)

    pub_keys = {(e.get('date'), e.get('group')) for e in unpublished}
    for e in all_entries:
        if (e.get('date'), e.get('group')) in pub_keys:
            e['published'] = True

    with open(entries_file, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    web_dest = _merge_to_changelog(unpublished)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin:main")]
    ])
    await callback.message.answer(f"✅ Опубликовано {len(unpublished)} записей. Публикую на сайт...", reply_markup=kb)
    await callback.answer()
    asyncio.create_task(_publish_changelog_via_api(web_dest, callback.message))
