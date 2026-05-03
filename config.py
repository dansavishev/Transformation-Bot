import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_TELEGRAM_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
    if x.strip().isdigit()
]

# OpenRouter / LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# ПРЕДЫДУЩАЯ МОДЕЛЬ: openai/gpt-oss-120b:free — заменена 2026-05-02
LLM_MODEL = "openai/gpt-4o-mini"
LLM_FALLBACK_MODEL = "openai/gpt-oss-120b:free"

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "bot.db"))

# ГОЛОСОВОЙ МОДУЛЬ ОТКЛЮЧЁН ВРЕМЕННО
# VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", str(BASE_DIR / "models" / "vosk-ru"))

# ChromaDB
CHROMA_PATH = str(BASE_DIR / "data" / "chroma")

# Prompts
PROMPTS_DIR = BASE_DIR / "prompts"
SITUATION_PROMPT_PATH = PROMPTS_DIR / "situation_prompt.yaml"
TRAINER_EVAL_PROMPT_PATH = PROMPTS_DIR / "trainer_eval_prompt.yaml"
SUMMARY_PROMPT_PATH = PROMPTS_DIR / "summary_prompt.yaml"

# History
HISTORY_LIMIT = 15

# RAG
RAG_TOP_K = 3

# Chunking
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

# Scheduler: daily summary at 03:00
SCHEDULER_HOUR = 3
SCHEDULER_MINUTE = 0
