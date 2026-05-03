# Прогресс разработки — Transformation Bot

## 30 апреля 2026

- Текст главного меню MAIN_MENU_TEXT обновлён (инструкция из 4 пунктов) → bot/handlers/onboarding.py
- Кнопка «🏋️ Тренажёр» удалена из main_menu_keyboard, осталась только «💬 Описать ситуацию» → bot/handlers/onboarding.py
- Текст enter_situation упрощён до одной строки → bot/handlers/situation.py
- После ответа LLM: убрана кнопка «Вернуться в меню», добавлено фиксированное сообщение «Давай потренируемся» + кнопка «💬 Описать ситуацию», FSM → in_trainer_answer → bot/handlers/situation.py
- Тренажёр полностью переработан: убран пайплайн симуляции (учебная ситуация → раунды), новый хэндлер trainer_answer оценивает варианты ответов пользователя через trainer_eval_prompt.yaml; контекст: situation_user_text + situation_bot_reply из FSMContext → bot/handlers/trainer.py, bot/states.py
- trainer_prompt.yaml удалён, константа TRAINER_PROMPT_PATH удалена; кнопка переименована в «🏋️ Тренажёр ответов» → config.py, admin_bot/handlers/prompts.py
- Накопление счётчика strong_scores_count: при оценке ≥8 +1, при достижении 3 — финальное сообщение + FSM → choosing_mode; сброс счётчика при новой ситуации → bot/handlers/trainer.py, situation.py
- Новый хэндлер choosing_mode_text: при тексте в choosing_mode показывает главное меню → bot/handlers/onboarding.py
- Голосовой ввод Vosk включён: bot/voice.py (синглтон модель, transcribe_ogg через ffmpeg), voice_handler.py (роутер для in_situation и in_trainer_answer), зарегистрирован до situation/trainer роутеров → bot/voice.py, bot/handlers/voice_handler.py, bot/main.py
- Баг pydub: OGG декодировался с тишиной → замена на прямой ffmpeg subprocess → bot/voice.py; pydub удалён → requirements.txt
- Баг frozen pydantic model: message.text = text → message.model_copy(update={"text": text}) → bot/handlers/voice_handler.py
- Двухшаговый pipeline ситуации: _diagnose_situation() (JSON через LLM) + _build_system_prompt_with_diagnosis() → bot/handlers/situation.py
- Сводка пользователя добавляется в system_prompt через get_summary(user_id) → bot/handlers/situation.py
- Ежедневный пересчёт сводок: create_summary(user_id, hours=None) вместо hours=24 → scheduler/daily_job.py

---

## 1 мая 2026

- Шаг 3 (пост-проверка) удалён: _postcheck_response() убрана, main_response → reply, экономия ~30% времени ответа → bot/handlers/situation.py
- Fallback-модели убраны: generate() теперь одноразовый вызов к LLM_MODEL, при ошибке исключение пробрасывается вверх → ai/llm_client.py
- completion_text: «Ты отлично справился...» → «Отлично! У тебя есть минимум три рабочих варианта из сильной позиции.» → bot/handlers/trainer.py
- Ошибка LLM в тренажёре: добавлена кнопка _situation_button() к сообщению об ошибке → bot/handlers/trainer.py
- Согласие проверяется в БД при /start: get_user_by_telegram_id() — если пользователь есть, согласие пропускается; новым — показывается CONSENT_TEXT → bot/handlers/onboarding.py
- CONSENT_TEXT: «историю» → «история» → bot/handlers/onboarding.py
- global_voice_fallback: _clear_last_keyboard() скрывает предыдущую кнопку, текст «Сначала нажми кнопку «Описать ситуацию»» → bot/handlers/voice_handler.py
- WELCOME_NEW и WELCOME_BACK удалены как мёртвый код → bot/handlers/onboarding.py
- Передача контекста диагностики между режимами: после шага 1 в situation.py диагностика сохраняется в FSMContext (mechanism, new_position, symptom, hidden_cause); в trainer.py контекст загружается и добавляется к system prompt перед оценкой варианта → bot/handlers/situation.py (160-174), bot/handlers/trainer.py (115-143, 161)

---

## 2 мая 2026

- Оформление сообщений: заголовки разделов в ситуации и тренажёре переведены с <blockquote> на <b>, добавлена логика удаления пустой строки после заголовка → bot/handlers/situation.py (127-144), bot/handlers/trainer.py (87-104). Первая цитата в тренажёре (фраза пользователя) остаётся в <blockquote>
- Смена LLM-модели: openai/gpt-oss-120b:free → openai/gpt-4o-mini через OpenRouter. Добавлен fallback на gpt-oss-120b при ошибке основной модели → config.py (LLM_MODEL, LLM_FALLBACK_MODEL), ai/llm_client.py
- Логирование скорости: добавлено логирование времени обработки каждого вызова LLM с форматом [TIMING] model=... elapsed=... prompt/completion/total токены → ai/llm_client.py. Замеры: диагностика ~3s, основной ответ ~5-12s, тренажёр ~3s
- Параметры модели: temperature=0.6, top_p=0.85 установлены для обеих моделей (основная и fallback) → ai/llm_client.py
- Баланс OpenRouter: добавлена кнопка "💰 Баланс OpenRouter" в админ-меню, выводит остаток в долларах ($X.XX) по API openrouter.ai/v1/credits → admin_bot/handlers/menu.py
- Исправлен формат промта: раздел "Почему стало неприятно" имел склейку текста с заголовком — добавлена пустая строка в prompts/situation_prompt.yaml (174)
- Четвёртый вариант ответа (⚠️ Рискованно) полностью убран из промта: удалены инструкции по варианту, раздел в проверке качества, четвёртый вариант из примера идеального ответа; осталось 2–3 варианта ответов → prompts/situation_prompt.yaml
- Форматирование разделов примера: добавлены пустые строки после заголовков "Почему стало неприятно:" и "Как можно было ответить:" для разделения от текста/вариантов ниже → prompts/situation_prompt.yaml
- Инициализация системы Changelog: создана структура папок (changelog, changelog/prompts, changelog/data, changelog/logs) → changelog/
- Файлы данных Changelog: processed_dates.json, pending.json, changelog.json → changelog/data/
- Создан промт переформулировки reformat_prompt.txt для LLM → changelog/prompts/
- Сайт изменений опубликован на GitHub Pages: index.html, styles.css, script.js, data/changelog.json в корне репо
- Интеграция Changelog в админ-бот: кнопка "📝 Выложить изменения" → просмотр pending, редактирование, сохранение в changelog.json → admin_bot/handlers/menu.py
- Watcher запущен как systemd-сервис transformation-bot-changelog: отслеживает progress.md, запускает pipeline extractor → transformer → changelog/watcher.py

---

## 2 мая 2026 (сессия — тестирование и исправление pipeline)

- **Архитектура Changelog завершена**: трёхэтапный pipeline progress.md → pending.json → changelog.json → GitHub Pages (каждый этап логируется в watcher.log)
- **Парсер исправлен**: changelog/parser.py переписан построчным чтением вместо regex с [a-zA-Z] (не работал с русским); формат: дата | группа → пункты • → JSON
- **GitHub API интеграция**: новый модуль changelog/github_api.py использует REST API PUT вместо git subprocess; атомарная публикация без конкурентных git lock-конфликтов
- **Удалено git-операции**: sync_to_github(pending.json) убрана из watcher.py; github_sync.py больше не импортируется; только API вызов из админ-бота при "Сохранить"
- **sync_to_web() сохранена**: копирует changelog.json из changelog/data/ в data/ (локальный кэш); GitHub API публикует в репо при "Сохранить"
- **Логирование в watcher**: [STEP 1-4] показывают progress: обнаружение изменения → найдено дат → LLM обработал → ожидание подтверждения админ-ботом
- **Edit changelog улучшен**: теперь отправляет реальный текущий pending как шаблон для редактирования вместо пустого примера → admin_bot/handlers/menu.py
- **Publish уведомление добавлено**: второе сообщение от бота с результатом: "✅ Сайт обновлён" или "⚠️ Ошибка: ..." → admin_bot/handlers/menu.py
- **Systemd updated**: transformation-bot-changelog читает GITHUB_TOKEN из .env через EnvironmentFile + load_dotenv в watcher.py (вместо hardcode в конфиге)
- **GITHUB_TOKEN добавлен**: Personal Access Token в .env (repo rights, https://github.com/settings/tokens)


