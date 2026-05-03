# Архив прогресса — Transformation Bot (до 28 апреля 2026)

## 21 апреля 2026

- vosk отключён, заглушка «временно недоступно» → ai/transcription.py, bot/handlers/situation.py
- streamlit удалён → requirements.txt
- venv пересобран CPU-only PyTorch
- Баг невалидного Markdown в ответе LLM → fallback без parse_mode → bot/handlers/situation.py
- Баг имени файла в базе знаний: index_file теперь принимает source_name → knowledge/indexer.py
- Admin bot: edit_reply_markup(None) во всех callback-хэндлерах, кнопки только в последнем сообщении → admin_bot/handlers/
- Admin bot база знаний: список документов нумерованный текстом, удаление по номеру → admin_bot/handlers/knowledge.py
- Admin bot диалоги: кнопки @username, Markdown-ссылки tg://user?id=ID, группировка по дням → admin_bot/handlers/dialogs.py
- Admin bot сводки: кнопки @username, «🔄 Обновить сводки» запускает hours=None → admin_bot/handlers/summaries.py
- БД: добавлена колонка username в users, автомиграция ALTER TABLE, get_or_create_user обновляет username → db/models.py, db/database.py, db/queries.py
- create_summary принимает hours=None, добавлен run_full_refresh() → scheduler/daily_job.py

---

## 21 апреля 2026 — сессия 2

- _clear_last_keyboard(bot, chat_id, state) + last_kbd_msg_id в FSMContext, кнопки только на последнем чанке → bot/handlers/onboarding.py
- _clear_last_keyboard применена во всех точках отправки с клавиатурой → bot/handlers/situation.py, trainer.py
- Промт оценки тренажёра: новый trainer_eval_prompt.yaml, TRAINER_EVAL_PROMPT_PATH, кнопка в админ-боте, оценка после фидбека → config.py, prompts/trainer_eval_prompt.yaml, admin_bot/handlers/prompts.py, bot/handlers/trainer.py

---

## 22 апреля 2026

- RAG, история, сводка закомментированы для тестирования чистого prompting → bot/handlers/situation.py
- LLM-модель: установлена openai/gpt-oss-120b:free (протестированы и отклонены qwen/llama/deepseek) → config.py
- _md_to_html(): >text → blockquote, ** → b, * → i; parse_mode Markdown → HTML; баг >**text** без пробела исправлен → bot/handlers/situation.py
- Admin bot редактор промтов: вывод частями по 3900 без обрезки, накопление частей в prompt_parts, кнопка «💾 Сохранить» → admin_bot/handlers/prompts.py

---

## 23 апреля 2026

- Баг: кнопка «Вернуться в меню» оставалась в старых сообщениях. callback-хэндлеры переведены на прямой edit_reply_markup(None), _clear_last_keyboard только в message-хэндлерах → bot/handlers/onboarding.py, situation.py, trainer.py
- Баг двойной кнопки «Сохранить» при вставке длинного промта: per-user asyncio.Lock в receive_new_prompt, старое сообщение удаляется delete_message, новое всегда снизу → admin_bot/handlers/prompts.py

---

## 26 апреля 2026

- Добавлен экран согласия: состояние UserFSM.consent, кнопка «Начать», сохранение login+время в data/consents/consents.txt → bot/states.py, bot/handlers/onboarding.py
- Обновлены тексты главного меню и режима «Описать ситуацию» → bot/handlers/onboarding.py, situation.py
- Механизм единого сообщения: consent_agree, back_to_menu, enter_situation используют edit_text вместо answer → bot/handlers/onboarding.py, situation.py

---

## 27 апреля 2026

- Systemd: убран ExecStartPre pkill (причина polling-конфликтов), TimeoutStopSec 10→20, добавлен ExecStopPost sleep 3 → /etc/systemd/system/transformation-bot.service
- ChromaDB warmup: asyncio.create_task(_warmup_bg()) вместо блокирующего executor → run.py
- Admin bot диалоги: PAGE_SIZE 20→10, убрана обрезка сообщений, накопительное добавление с лимитом 4096, кнопка «Загрузить ещё ⬆️» только если есть старые → admin_bot/handlers/dialogs.py
- Ленивая загрузка: knowledge.router отключён в admin_bot/main.py; chromadb и ONNXMiniLM_L6_V2 перенесены внутрь _get_collection() → admin_bot/main.py, ai/rag.py
