import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from config import TELEGRAM_TOKEN
from bot.handlers import onboarding, situation, trainer, voice_handler

logger = logging.getLogger(__name__)


async def _ignore_stale_callback(event: ErrorEvent) -> None:
    if isinstance(event.exception, TelegramBadRequest) and "query is too old" in str(event.exception):
        logger.debug("Ignored stale callback query: %s", event.exception)
        return
    raise event.exception


def create_user_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.errors.register(_ignore_stale_callback)
    dp.include_router(onboarding.router)
    dp.include_router(voice_handler.router)
    dp.include_router(situation.router)
    dp.include_router(trainer.router)
    return bot, dp
