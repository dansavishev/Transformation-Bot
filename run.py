import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    from db.database import init_db
    from bot.main import create_user_bot
    from admin_bot.main import create_admin_bot
    from scheduler.daily_job import setup_scheduler

    init_db()
    logger.info("Database initialized")

    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started (daily summary at 03:00)")

    async def _warmup_bg():
        from ai.rag import _get_collection
        try:
            await asyncio.to_thread(_get_collection)
            logger.info("ChromaDB warmed up successfully")
        except Exception as e:
            logger.warning("ChromaDB warmup failed: %s", e)

    asyncio.create_task(_warmup_bg())

    user_bot, user_dp = create_user_bot()
    admin_bot, admin_dp = create_admin_bot()

    logger.info("Starting both bots...")
    await asyncio.gather(
        user_dp.start_polling(user_bot, allowed_updates=["message", "callback_query"]),
        admin_dp.start_polling(admin_bot, allowed_updates=["message", "callback_query"]),
    )


if __name__ == "__main__":
    asyncio.run(main())
