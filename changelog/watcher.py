#!/usr/bin/env python3
"""
Следит за изменением progress.md и автоматически запускает pipeline
"""
import os
import sys
import time
import logging
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Загружаем .env из корня проекта
_project_root = Path(__file__).parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

# Добавляем папку changelog в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from extractor import get_new_changes, save_processed_dates
from transformer import process_changes

# Логирование
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Changelog Watcher")

def sync_to_web(changelog_dir, project_dir):
    """Синхронизирует changelog.json в корневой data/ для веб-сайта"""
    try:
        source = Path(changelog_dir) / "data" / "changelog.json"
        dest = Path(project_dir) / "data" / "changelog.json"

        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            logger.info(f"✅ Синхронизирован веб-сайт: {dest}")
    except Exception as e:
        logger.warning(f"⚠️  Ошибка синхронизации веб-сайта: {e}")

class ProgressFileHandler(FileSystemEventHandler):
    def __init__(self, progress_path, changelog_dir, llm_model, api_key, project_dir):
        self.progress_path = progress_path
        self.changelog_dir = changelog_dir
        self.llm_model = llm_model
        self.api_key = api_key
        self.project_dir = project_dir
        self.last_trigger = 0
        self.debounce_delay = 5  # Дебаунс 5 секунд

    def on_modified(self, event):
        # Проверяем что это progress.md
        if not event.src_path.endswith("progress.md"):
            return
        
        # Дебаунс: не обрабатываем слишком частые срабатывания
        now = time.time()
        if now - self.last_trigger < self.debounce_delay:
            return
        
        self.last_trigger = now
        
        # Небольшая задержка (файл может ещё писаться)
        time.sleep(2)
        
        logger.info("[STEP 1] progress.md изменён, начало обработки...")

        processed_file = Path(self.changelog_dir) / "data" / "processed_dates.json"

        try:
            # Выделяем новые изменения
            new_changes = get_new_changes(self.progress_path, str(processed_file))

            if not new_changes:
                logger.info("[STEP 2] Новых изменений нет — все даты уже обработаны")
                return

            dates_found = [c['date_normalized'] for c in new_changes]
            logger.info(f"[STEP 2] Найдено новых дат: {len(new_changes)} — {dates_found}")

            # Обрабатываем через LLM
            logger.info(f"[STEP 3] Отправка в LLM ({self.llm_model})...")
            success = process_changes(
                new_changes,
                self.llm_model,
                self.api_key,
                self.changelog_dir
            )

            if success:
                pending_count = 0
                pending_file = Path(self.changelog_dir) / "data" / "pending.json"
                try:
                    import json
                    with open(pending_file) as f:
                        pending_count = len(json.load(f))
                except Exception:
                    pass
                logger.info(f"[STEP 3] LLM обработал успешно. pending.json содержит {pending_count} записей")
                logger.info("[STEP 4] Pipeline завершён. Ожидание подтверждения в адмн-боте.")
            else:
                logger.warning("[STEP 3] Pipeline завершился с ошибками — LLM не вернул результат")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке: {e}", exc_info=True)

def main():
    # Читаем вводные из окружения
    progress_path = Path(os.getenv("PROGRESS_PATH", "/opt/transformation-bot/progress.md"))
    changelog_dir = Path(os.getenv("CHANGELOG_DIR", "/opt/transformation-bot/changelog"))
    llm_model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b:free")
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    project_dir = Path(os.getenv("PROJECT_DIR", "/opt/transformation-bot"))
    
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY не установлен")
        sys.exit(1)
    
    if not progress_path.exists():
        logger.error(f"❌ progress.md не найден: {progress_path}")
        sys.exit(1)
    
    logger.info("🚀 Запуск Changelog Watcher")
    logger.info(f"   progress.md: {progress_path}")
    logger.info(f"   changelog_dir: {changelog_dir}")
    logger.info(f"   LLM модель: {llm_model}")
    
    # Создаём observer
    event_handler = ProgressFileHandler(progress_path, changelog_dir, llm_model, api_key, project_dir)
    observer = Observer()
    observer.schedule(event_handler, path=str(progress_path.parent), recursive=False)
    observer.start()
    
    logger.info("✅ Watcher запущен. Ожидание изменений...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("🛑 Watcher остановлен")
    
    observer.join()

if __name__ == "__main__":
    main()
