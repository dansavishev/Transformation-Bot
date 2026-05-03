import logging
import re
import yaml
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.states import UserFSM
from bot.handlers.onboarding import _clear_last_keyboard
from config import TRAINER_EVAL_PROMPT_PATH
from db.queries import get_or_create_user, save_message
from ai.llm_client import generate

logger = logging.getLogger(__name__)
router = Router()


def _situation_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Описать ситуацию", callback_data="mode:situation")]
    ])


def _load_eval_prompt() -> str:
    with open(TRAINER_EVAL_PROMPT_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("system_prompt", "") or ""


def _parse_variants(text: str) -> list[str]:
    text = text.strip()
    # Нумерованный список: "1. " или "1) "
    numbered = re.split(r'\n(?=\d+[.)]\s)', text)
    if len(numbered) > 1:
        variants = []
        for item in numbered:
            item = re.sub(r'^\d+[.)]\s+', '', item.strip())
            if item:
                variants.append(item)
        return variants
    # По двойным переносам (пустая строка)
    by_double = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    if len(by_double) > 1:
        return by_double
    # По одиночным переносам — только если каждая часть короткая (обычная реплика)
    by_single = [p.strip() for p in text.split('\n') if p.strip()]
    if len(by_single) > 1 and all(len(p) < 250 for p in by_single):
        return by_single
    return [text]


def _extract_score(text: str) -> int:
    matches = re.findall(r'>?\*\*Оценка:\*\*\s*(\d+)/10', text)
    if matches:
        return int(matches[0])
    return 5


def _closing_text(score: int) -> str:
    if score >= 8:
        return (
            "Сильный ответ. Здесь чувствуется взрослая позиция.\n\n"
            "Давай закрепим навык — напиши ещё варианты ответа."
        )
    elif score >= 5:
        return (
            "Неплохо, но ещё чувствуется старая реакция.\n\n"
            "Покажи новые варианты ответа из сильной позиции."
        )
    else:
        return (
            "Сейчас ответ больше идёт из защиты, чем из силы. "
            "Это нормально — навык ещё формируется.\n\n"
            "Попробуй написать ещё несколько новых вариантов из сильной позиции."
        )


def _split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    while text:
        parts.append(text[:limit])
        text = text[limit:]
    return parts


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


@router.message(UserFSM.in_trainer_answer, F.text)
async def trainer_answer(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    user_id = get_or_create_user(telegram_id, message.from_user.first_name, message.from_user.username)

    data = await state.get_data()
    situation_user_text = data.get("situation_user_text", "")
    situation_bot_reply = data.get("situation_bot_reply", "")
    mechanism = data.get("diagnosis_mechanism", "")
    new_position = data.get("diagnosis_new_position", "")
    symptom = data.get("diagnosis_symptom", "")
    hidden_cause = data.get("diagnosis_hidden_cause", "")
    user_answer = message.text.strip()

    variants = _parse_variants(user_answer)
    eval_prompt = _load_eval_prompt()

    # Добавить контекст диагностики к system prompt
    context_block = ""
    if mechanism or new_position:
        context_block = f"""

---

КОНТЕКСТ СИТУАЦИИ И РАЗБОРА:

Ситуация пользователя: {situation_user_text}

Механизм: {mechanism}
Симптом и скрытая причина: {symptom} → {hidden_cause}
Новая позиция из разбора: {new_position}

Используй этот контекст как готовый факт при оценке вариантов.
Не пересчитывай механизм и новую позицию заново.
"""
        logger.info("TRAINER CONTEXT: mechanism=%s | symptom=%s | hidden_cause=%s | new_position=%s",
                    mechanism, symptom, hidden_cause, new_position)

    full_system = eval_prompt + context_block

    save_message(user_id, "user", f"[ТРЕНАЖЁР] {user_answer}")
    await _clear_last_keyboard(message.bot, message.chat.id, state)

    strong_scores_count = data.get("strong_scores_count", 0)
    last_score = 5

    for variant in variants:
        messages = []
        if situation_user_text:
            messages.append({"role": "user", "content": situation_user_text})
        if situation_bot_reply:
            messages.append({"role": "assistant", "content": situation_bot_reply})
        messages.append({"role": "user", "content": variant})

        try:
            await message.bot.send_chat_action(message.chat.id, "typing")
            feedback = await generate(full_system, messages)
        except Exception as exc:
            logger.error("Trainer eval LLM error for user %d: %s", telegram_id, exc)
            await message.answer("Прости, что-то пошло не так. Попробуй снова через минуту.", reply_markup=_situation_button())
            return

        save_message(user_id, "assistant", f"[ОЦЕНКА] {feedback}")
        last_score = _extract_score(feedback)
        if last_score >= 8:
            strong_scores_count += 1

        quote_html = f"<blockquote>{variant}</blockquote>\n\n"
        feedback_html = quote_html + _md_to_html(feedback)

        for chunk in _split_message(feedback_html):
            try:
                await message.answer(chunk, parse_mode="HTML")
            except Exception:
                await message.answer(chunk)

    await state.update_data(strong_scores_count=strong_scores_count)

    # Финальное сообщение если набрано 3 сильных ответа (≥8) по этой ситуации
    if strong_scores_count >= 3:
        completion_text = (
            "Отлично! У тебя есть минимум три рабочих варианта из сильной позиции.\n"
            "Закрепи их в себе и отстаивай свои личные границы по-новому!\n\n"
            "Если хочешь разобрать новую ситуацию - нажми кнопку и записывай сообщение."
        )
        sent = await message.answer(completion_text, reply_markup=_situation_button())
        await state.set_state(UserFSM.choosing_mode)
    else:
        closing = _closing_text(last_score)
        sent = await message.answer(closing, reply_markup=_situation_button())

    await state.update_data(last_kbd_msg_id=sent.message_id)
