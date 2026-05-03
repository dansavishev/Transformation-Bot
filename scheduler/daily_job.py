import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import SCHEDULER_HOUR, SCHEDULER_MINUTE
from db.queries import get_users_active_since
from ai.summarizer import create_summary

logger = logging.getLogger(__name__)


async def run_daily() -> None:
    logger.info("Daily summary job started")
    user_ids = get_users_active_since(hours=24)
    logger.info("Active users in last 24h: %d", len(user_ids))
    for user_id in user_ids:
        try:
            await create_summary(user_id, hours=None)
        except Exception as exc:
            logger.error("Failed summary for user %d: %s", user_id, exc)
    logger.info("Daily summary job finished")


async def run_full_refresh() -> int:
    from db.queries import get_all_users
    all_users = get_all_users()
    logger.info("Full summary refresh for %d users", len(all_users))
    count = 0
    for u in all_users:
        try:
            result = await create_summary(u["user_id"], hours=None)
            if result:
                count += 1
        except Exception as exc:
            logger.error("Failed full refresh for user %d: %s", u["user_id"], exc)
    logger.info("Full refresh done: %d summaries updated", count)
    return count


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_daily,
        trigger="cron",
        hour=SCHEDULER_HOUR,
        minute=SCHEDULER_MINUTE,
        id="daily_summary",
        replace_existing=True,
    )
    return scheduler
