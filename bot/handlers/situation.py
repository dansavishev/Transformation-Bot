import logging
import re
import json
import yaml
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import UserFSM
from bot.handlers.onboarding import _clear_last_keyboard
from config import SITUATION_PROMPT_PATH, HISTORY_LIMIT
from db.queries import get_or_create_user, save_message, get_history, get_summary
from ai.llm_client import generate
from ai.rag import search

logger = logging.getLogger(__name__)
router = Router()


def _back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="menu:main")]
    ])


def _describe_new_situation_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Описать ситуацию", callback_data="mode:situation")]
    ])


def _load_situation_prompt() -> str:
    with open(SITUATION_PROMPT_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("system_prompt", "")


def _build_context(system_prompt: str, history: list[dict], summary: str | None, rag_docs: list[str]) -> str:
    parts = [system_prompt]
    if summary:
        parts.append(f"\n--- СВОДКА О ПОЛЬЗОВАТЕЛЕ ---\n{summary}\n")
    if rag_docs:
        joined = "\n\n".join(rag_docs)
        parts.append(f"\n--- МАТЕРИАЛЫ ИЗ БАЗЫ ЗНАНИЙ ---\n{joined}\n")
    return "\n".join(parts)


async def _diagnose_situation(text: str) -> dict | None:
    """Шаг 1: Диагностика ситуации (скрытый вызов)."""
    diagnosis_prompt = """Ты — аналитик психологических ситуаций. Твоя задача — провести точную
диагностику ситуации пользователя перед формированием ответа.

Прочитай ситуацию внимательно. Используй только то что есть в тексте —
не додумывай и не приписывай то чего пользователь не описывал.

Определи и верни строго в формате JSON без лишнего текста:

{
  "mechanism": "Точный психологический механизм ситуации одним предложением",
  "internal_translation": [
    "Первая строка внутреннего перевода — строго из слов и чувств пользователя",
    "Вторая строка если прямо следует из текста, иначе пустая строка"
  ],
  "symptom": "Один симптом поведения пользователя из его описания",
  "hidden_cause": "Скрытая причина реакции пользователя одной фразой",
  "new_position": "Новая позиция которую важно донести — конкретное утверждение",
  "is_recurring_pattern": true или false,
  "recurring_pattern_description": "Описание паттерна если is_recurring_pattern = true, иначе пустая строка"
}"""

    try:
        diagnosis_text = await generate(diagnosis_prompt, [{"role": "user", "content": text}])
        diagnosis_json = json.loads(diagnosis_text)
        return diagnosis_json
    except Exception as exc:
        logger.warning("Diagnosis step failed: %s", exc)
        return None


def _build_system_prompt_with_diagnosis(base_prompt: str, diagnosis: dict | None, summary: str | None) -> str:
    """Шаг 2: Собрать system_prompt с диагностикой и сводкой."""
    parts = [base_prompt]

    if diagnosis is not None:
        internal_trans = "\n".join(
            line for line in diagnosis.get("internal_translation", []) if line.strip()
        )
        recurring_desc = diagnosis.get("recurring_pattern_description", "")
        if not diagnosis.get("is_recurring_pattern", False):
            recurring_desc = "не выявлен"

        diagnosis_block = f"""
---

ДИАГНОСТИКА ЭТОЙ СИТУАЦИИ:

Механизм: {diagnosis.get('mechanism', '')}

Внутренний перевод пользователя:
{internal_trans}

Симптом и скрытая причина: {diagnosis.get('symptom', '')} → {diagnosis.get('hidden_cause', '')}

Новая позиция для главного сдвига: {diagnosis.get('new_position', '')}

Повторяющийся паттерн: {recurring_desc}

Используй диагностику выше как готовый факт — не пересчитывай.
Твоя задача — написать живой ответ на основе уже проведённого анализа."""
        parts.append(diagnosis_block)

    if summary:
        summary_block = f"""
---

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ ИЗ ИСТОРИИ:

{summary}

Используй контекст чтобы усилить точность блоков
"Твоя позиция в моменте" и "Главный сдвиг".
Если история показывает повторяющийся паттерн — назови его явно."""
        parts.append(summary_block)

    return "\n".join(parts)


def _md_to_html(text: str) -> str:
    def escape(s: str) -> str:
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    lines = []
    prev_was_header = False
    for line in text.split('\n'):
        if line.startswith('>'):
            content = line[1:].lstrip(' ')
            content = escape(content)
            content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
            content = re.sub(r'\*(.+?)\*', r'<i>\1</i>', content)
            lines.append(f'<b>{content}</b>')
            prev_was_header = True
        else:
            if prev_was_header and line.strip() == '':
                continue
            line = escape(line)
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
            lines.append(line)
            prev_was_header = False
    return '\n'.join(lines)


async def _handle_text(text: str, user_id: int, state: FSMContext, message: Message) -> None:
    save_message(user_id, "user", text)
    await state.update_data(situation_user_text=text, strong_scores_count=0)

    base_prompt = _load_situation_prompt()
    summary = get_summary(user_id)

    try:
        await message.bot.send_chat_action(message.chat.id, "typing")

        # ШАГ 1: Диагностика
        diagnosis = await _diagnose_situation(text)
        if diagnosis:
            logger.info("DIAGNOSIS: mechanism=%s | symptom=%s | hidden_cause=%s | new_position=%s",
                        diagnosis.get("mechanism", ""), diagnosis.get("symptom", ""),
                        diagnosis.get("hidden_cause", ""), diagnosis.get("new_position", ""))

        # Сохранить диагностику в FSMContext для передачи в тренажёр
        if diagnosis is not None:
            await state.update_data(
                diagnosis_mechanism=diagnosis.get("mechanism", ""),
                diagnosis_new_position=diagnosis.get("new_position", ""),
                diagnosis_symptom=diagnosis.get("symptom", ""),
                diagnosis_hidden_cause=diagnosis.get("hidden_cause", "")
            )
        else:
            await state.update_data(
                diagnosis_mechanism="",
                diagnosis_new_position="",
                diagnosis_symptom="",
                diagnosis_hidden_cause=""
            )

        # ШАГ 2: Основной ответ
        system_prompt = _build_system_prompt_with_diagnosis(base_prompt, diagnosis, summary)
        reply = await generate(system_prompt, [{"role": "user", "content": text}])

    except Exception as exc:
        logger.error("LLM error for user %d: %s", user_id, exc)
        await _clear_last_keyboard(message.bot, message.chat.id, state)
        sent = await message.answer(
            "Прости, что-то пошло не так. Попробуй снова через минуту.",
            reply_markup=_back_button(),
        )
        await state.update_data(last_kbd_msg_id=sent.message_id)
        return

    save_message(user_id, "assistant", reply)
    await state.update_data(situation_bot_reply=reply)
    html_reply = _md_to_html(reply)

    chunks = _split_message(html_reply)
    await _clear_last_keyboard(message.bot, message.chat.id, state)
    for chunk in chunks:
        try:
            await message.answer(chunk, parse_mode="HTML")
        except Exception:
            await message.answer(chunk)

    # Фиксированное сообщение с предложением потренироваться
    training_text = (
        "Давай потренируемся.\n\n"
        "Напиши в следующем сообщении три варианта - как бы ты ответил в этой ситуации по-новому.\n\n"
        "Каждый вариант пиши с новой строки или пронумеруй их.\n\n"
        "Если хочешь разобрать новую ситуацию - нажми кнопку и записывай сообщение."
    )
    sent = await message.answer(training_text, reply_markup=_describe_new_situation_button())
    await state.update_data(last_kbd_msg_id=sent.message_id)
    await state.set_state(UserFSM.in_trainer_answer)


def _split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        parts.append(text[:limit])
        text = text[limit:]
    return parts


@router.callback_query(lambda c: c.data == "mode:situation")
async def enter_situation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserFSM.in_situation)
    try:
        await callback.message.edit_text(
            "Расскажи о своей ситуации - текстом или голосовым сообщением."
        )
    except Exception:
        pass
    await callback.answer()


@router.message(UserFSM.in_situation, F.text)
async def situation_text(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    user_id = get_or_create_user(telegram_id, message.from_user.first_name, message.from_user.username)
    await _handle_text(message.text.strip(), user_id, state, message)


