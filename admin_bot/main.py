import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject, Message, CallbackQuery, ErrorEvent
from typing import Callable, Awaitable, Any
from config import ADMIN_BOT_TOKEN, ADMIN_TELEGRAM_IDS
from admin_bot.handlers import menu, dialogs, prompts, summaries

logger = logging.getLogger(__name__)


class AdminAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is not None and user_id not in ADMIN_TELEGRAM_IDS:
            if isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён.", show_alert=True)
            return

        return await handler(event, data)


async def _ignore_stale_callback(event: ErrorEvent) -> None:
    if isinstance(event.exception, TelegramBadRequest) and "query is too old" in str(event.exception):
        logger.debug("Ignored stale callback query: %s", event.exception)
        return
    raise event.exception


def create_admin_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=ADMIN_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AdminAccessMiddleware())
    dp.callback_query.middleware(AdminAccessMiddleware())
    dp.errors.register(_ignore_stale_callback)

    dp.include_router(menu.router)
    dp.include_router(dialogs.router)
    dp.include_router(prompts.router)
    # dp.include_router(knowledge.router)
    dp.include_router(summaries.router)

    return bot, dp
