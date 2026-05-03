import logging
import yaml
from config import SUMMARY_PROMPT_PATH
from ai.llm_client import generate
from db.queries import get_messages_since, update_summary

logger = logging.getLogger(__name__)


def _load_summary_prompt() -> str:
    with open(SUMMARY_PROMPT_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("system_prompt", "")


async def create_summary(user_id: int, hours: int | None = 24) -> str:
    messages = get_messages_since(user_id, hours=hours)
    if not messages:
        logger.info("No messages for user %d in last 24h, skipping summary", user_id)
        return ""

    system_prompt = _load_summary_prompt()
    dialog_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )
    llm_messages = [{"role": "user", "content": dialog_text}]

    try:
        summary = await generate(system_prompt, llm_messages)
        update_summary(user_id, summary)
        logger.info("Summary created for user %d", user_id)
        return summary
    except Exception as exc:
        logger.error("Failed to create summary for user %d: %s", user_id, exc)
        return ""
