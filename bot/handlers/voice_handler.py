import os
import logging
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states import UserFSM
from bot.voice import transcribe_ogg
from bot.handlers.situation import situation_text
from bot.handlers.trainer import trainer_answer
from bot.handlers.onboarding import _clear_last_keyboard

router = Router()
logger = logging.getLogger(__name__)

async def _voice_to_message(message: Message, bot: Bot, state: FSMContext, handler):
    ogg_path = f"/tmp/{message.voice.file_id}.ogg"
    try:
        file = await bot.get_file(message.voice.file_id)
        await bot.download_file(file.file_path, ogg_path)

        text = transcribe_ogg(ogg_path)

        if not text:
            await message.answer("Не удалось распознать голосовое сообщение. Попробуй ещё раз или напиши текстом.")
            return

        # Создаём копию с текстом (Message frozen в pydantic v2)
        await handler(message.model_copy(update={"text": text}), state)

    except Exception as e:
        logger.exception("Ошибка обработки голосового сообщения")
        await message.answer("Произошла ошибка при распознавании. Напиши текстом.")
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)


@router.message(UserFSM.in_situation, F.voice)
async def voice_situation(message: Message, bot: Bot, state: FSMContext):
    await _voice_to_message(message, bot, state, situation_text)


@router.message(UserFSM.in_trainer_answer, F.voice)
async def voice_trainer(message: Message, bot: Bot, state: FSMContext):
    await _voice_to_message(message, bot, state, trainer_answer)


@router.message(F.voice)
async def global_voice_fallback(message: Message, state: FSMContext, bot: Bot) -> None:
    await _clear_last_keyboard(message, message.chat.id, state, bot)
    await message.answer(
        "Сначала нажми кнопку «Описать ситуацию».",
    )
