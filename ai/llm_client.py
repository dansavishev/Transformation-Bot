import logging
import time
from openai import AsyncOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, LLM_MODEL, LLM_FALLBACK_MODEL

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    return _client


async def generate(system_prompt: str, messages: list[dict]) -> str:
    """Send request to OpenRouter. On primary model failure falls back to LLM_FALLBACK_MODEL."""
    client = _get_client()
    payload = [{"role": "system", "content": system_prompt}] + messages

    start = time.time()
    model_used = LLM_MODEL
    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=payload,
            temperature=0.6,
            top_p=0.85,
        )
    except Exception as exc:
        logger.warning("Primary model %s failed: %s — switching to fallback %s", LLM_MODEL, exc, LLM_FALLBACK_MODEL)
        model_used = LLM_FALLBACK_MODEL
        response = await client.chat.completions.create(
            model=LLM_FALLBACK_MODEL,
            messages=payload,
            temperature=0.6,
            top_p=0.85,
        )

    elapsed = time.time() - start
    text = response.choices[0].message.content or ""
    usage = response.usage
    if usage:
        logger.info(
            "[TIMING] model=%s elapsed=%.2fs prompt=%s completion=%s total=%s",
            model_used, elapsed, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    else:
        logger.info("[TIMING] model=%s elapsed=%.2fs (no usage data)", model_used, elapsed)
    return text.strip()
