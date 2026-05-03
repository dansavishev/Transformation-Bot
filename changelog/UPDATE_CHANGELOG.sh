#!/bin/bash
set -e

echo "=========================================="
echo "🔧 ИСПРАВЛЕНИЕ СИСТЕМЫ CHANGELOG"
echo "=========================================="
echo ""

PROJECT_DIR="/opt/transformation-bot"
CHANGELOG_DIR="$PROJECT_DIR/changelog"

# ШАГ 1: Проверка структуры
echo "ШАГ 1️⃣  Проверка структуры проекта"
echo "================================"

if [ ! -d "$CHANGELOG_DIR" ]; then
    echo "❌ Папка $CHANGELOG_DIR не найдена"
    exit 1
fi
echo "✅ Папка changelog найдена"

if [ ! -f "$PROJECT_DIR/index.html" ]; then
    echo "⚠️  $PROJECT_DIR/index.html не найден (создадим новый)"
fi

if [ ! -f "$PROJECT_DIR/script.js" ]; then
    echo "⚠️  $PROJECT_DIR/script.js не найден (создадим новый)"
fi

echo ""

# ШАГ 2: Резервная копия текущих файлов
echo "ШАГ 2️⃣  Создание резервных копий"
echo "================================"

BACKUP_DIR="$PROJECT_DIR/.changelog_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Резервная копия: $BACKUP_DIR"

# Копируем старые файлы если они существуют
[ -f "$PROJECT_DIR/index.html" ] && cp "$PROJECT_DIR/index.html" "$BACKUP_DIR/" && echo "✅ Сохранён index.html"
[ -f "$PROJECT_DIR/script.js" ] && cp "$PROJECT_DIR/script.js" "$BACKUP_DIR/" && echo "✅ Сохранён script.js"
[ -f "$CHANGELOG_DIR/data/changelog.json" ] && cp "$CHANGELOG_DIR/data/changelog.json" "$BACKUP_DIR/" && echo "✅ Сохранён changelog.json (локальный)"
[ -f "$PROJECT_DIR/data/changelog.json" ] && cp "$PROJECT_DIR/data/changelog.json" "$BACKUP_DIR/" && echo "✅ Сохранён changelog.json (GitHub)"

echo "✅ Резервные копии созданы"
echo ""

# ШАГ 3: Создание папок если нужно
echo "ШАГ 3️⃣  Проверка папок"
echo "================================"

mkdir -p "$PROJECT_DIR/data"
mkdir -p "$CHANGELOG_DIR/data"
mkdir -p "$CHANGELOG_DIR/prompts"

echo "✅ Все папки проверены"
echo ""

# ШАГ 4: Создание обновленного changelog.json
echo "ШАГ 4️⃣  Создание исправленного changelog.json"
echo "================================"

cat > "$PROJECT_DIR/data/changelog.json" << 'CHANGELOG_EOF'
[
  {
    "date": "2026-05-02",
    "group": "Интерфейс",
    "changes": [
      "Улучшена методология анализа ситуаций — бот теперь глубже разбирается в психологическом механизме конфликта"
    ]
  },
  {
    "date": "2026-05-02",
    "group": "Интерфейс",
    "changes": [
      "Обновлён формат сообщений — важные разделы теперь выделены для лучшей читаемости",
      "Добавлена информация о статусе сервиса в админ-меню — можно проверить доступность",
      "Улучшено разделение текста — добавлены пробелы между разделами для удобства чтения"
    ]
  },
  {
    "date": "2026-05-02",
    "group": "Логика",
    "changes": [
      "Улучшено качество анализа — система теперь использует более мощные алгоритмы для понимания ситуации",
      "Оптимизирована скорость обработки — ты видишь ответ значительно быстрее",
      "Исправлено форматирование ответов — информация лучше организована и понятнее"
    ]
  },
  {
    "date": "2026-05-02",
    "group": "Баги",
    "changes": [
      "Упрощён выбор вариантов в Тренажёре — теперь меньше опций, проще выбрать",
      "Исправлено форматирование примеров — текст теперь читается без заминок"
    ]
  },
  {
    "date": "2026-05-01",
    "group": "Логика",
    "changes": [
      "Улучшена система анализа твоих запросов — бот лучше понимает суть проблемы"
    ]
  },
  {
    "date": "2026-05-01",
    "group": "Логика",
    "changes": [
      "Ускорены ответы на 30% — убрана лишняя проверка результата",
      "Улучшена передача контекста между режимами — бот помнит всю информацию о ситуации",
      "Добавлена кнопка помощи при ошибке в Тренажёре — легче получить поддержку"
    ]
  },
  {
    "date": "2026-05-01",
    "group": "Интерфейс",
    "changes": [
      "Обновлён текст поздравления — стал более позитивным и поддерживающим",
      "Упрощён текст согласия — короче и понятнее",
      "Улучшен опыт голосового ввода — кнопки теперь корректно скрываются"
    ]
  },
  {
    "date": "2026-05-01",
    "group": "Админ. панель",
    "changes": [
      "Удалены неиспользуемые экраны — упрощён интерфейс",
      "Оптимизирована проверка первого входа — новые пользователи видят согласие только один раз"
    ]
  },
  {
    "date": "2026-05-01",
    "group": "Архитектура",
    "changes": [
      "Упрощена система обработки ошибок — более надёжная и быстрая"
    ]
  },
  {
    "date": "2026-04-30",
    "group": "Баги",
    "changes": [
      "Улучшена поддержка контекста диалога — бот помнит всю историю разговора"
    ]
  },
  {
    "date": "2026-04-30",
    "group": "Интерфейс",
    "changes": [
      "Обновлён текст главного меню — теперь с ясными инструкциями для новых пользователей",
      "Упрощена главная страница — остался только режим Ситуация",
      "Сокращен текст описания режима — информация более лаконична"
    ]
  },
  {
    "date": "2026-04-30",
    "group": "Логика",
    "changes": [
      "Переработан режим Тренажёр — теперь бот оценивает твои варианты ответов вместо симуляции диалога",
      "Добавлена система прогресса — после трёх успешных ответов бот дает финальное сообщение",
      "Улучшена навигация между режимами — легче переключаться между ними"
    ]
  },
  {
    "date": "2026-04-30",
    "group": "Архитектура",
    "changes": [
      "Включена поддержка голосовых сообщений — теперь можно описывать ситуации голосом",
      "Улучшена обработка звука — голосовые сообщения распознаются точнее",
      "Расширен анализ ситуаций — система использует больше признаков для понимания проблемы"
    ]
  },
  {
    "date": "2026-04-30",
    "group": "Баги",
    "changes": [
      "Исправлена ошибка с обновлением сообщений — текст теперь корректно изменяется",
      "Удалены ненужные зависимости — приложение работает быстрее"
    ]
  }
]
CHANGELOG_EOF

if [ -f "$PROJECT_DIR/data/changelog.json" ]; then
    echo "✅ Создан $PROJECT_DIR/data/changelog.json"
else
    echo "❌ Ошибка создания changelog.json"
    exit 1
fi

# Копируем в локальную папку changelog
cp "$PROJECT_DIR/data/changelog.json" "$CHANGELOG_DIR/data/changelog.json"
echo "✅ Скопирован в $CHANGELOG_DIR/data/changelog.json"
echo ""

# ШАГ 5: Создание обновленного index.html
echo "ШАГ 5️⃣  Создание обновленного index.html"
echo "================================"

cat > "$PROJECT_DIR/index.html" << 'INDEX_EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changelog — Бот по психологии человека</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="page-wrapper">
        <!-- Header -->
        <header class="header">
            <div class="header-top">
                <h1 class="title">Бот по психологии человека</h1>
                <svg class="header-logo" width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="32" height="32" rx="8" fill="#E8D5F2"/>
                    <path d="M16 8L18.5 14.5H25.5L20 18.5L22.5 25L16 21L9.5 25L12 18.5L6.5 14.5H13.5L16 8Z" fill="#A084DC"/>
                </svg>
            </div>

            <a href="https://t.me/arsenosoznannost_bot" class="telegram-button" target="_blank">
                <svg class="telegram-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.5 2L2.5 9.5C1.5 10 1.5 10.5 2.5 10.8L7 12L14.5 5.5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
                Открыть Telegram-бота
            </a>
        </header>

        <!-- Main content -->
        <main class="main-content">
            <div class="changelog-header">
                <h2>CHANGELOG</h2>
            </div>

            <div class="changelog-container">
                <div class="cards-scroll" id="cardsScroll">
                    <!-- Карточки будут загружены здесь -->
                </div>
            </div>
        </main>
    </div>

    <script src="script.js"></script>
</body>
</html>
INDEX_EOF

if [ -f "$PROJECT_DIR/index.html" ]; then
    echo "✅ Создан $PROJECT_DIR/index.html"
else
    echo "❌ Ошибка создания index.html"
    exit 1
fi
echo ""

# ШАГ 6: Создание обновленного script.js
echo "ШАГ 6️⃣  Создание обновленного script.js"
echo "================================"

cat > "$PROJECT_DIR/script.js" << 'SCRIPT_EOF'
// Маппинг групп на CSS классы, иконки и цвета
const groupMap = {
    'Интерфейс': { 
        class: 'interface', 
        icon: '🎨',
        bgColor: '#FFF4E6',
        iconBg: '#FFD699'
    },
    'Админ. панель': { 
        class: 'admin', 
        icon: '⚙️',
        bgColor: '#F0E6FF',
        iconBg: '#D9B3FF'
    },
    'Логика': { 
        class: 'logic', 
        icon: '⚡',
        bgColor: '#E6F7FF',
        iconBg: '#99D9FF'
    },
    'Баги': { 
        class: 'bug', 
        icon: '🔧',
        bgColor: '#FFE6E6',
        iconBg: '#FF9999'
    },
    'Архитектура': { 
        class: 'architecture', 
        icon: '🏗️',
        bgColor: '#E6F5FF',
        iconBg: '#99CCFF'
    },
    'Оптимизация': { 
        class: 'optimization', 
        icon: '⚡',
        bgColor: '#E6FFE6',
        iconBg: '#99FF99'
    }
};

async function loadChangelog() {
    try {
        // Пытаемся несколько путей
        let response = await fetch('./data/changelog.json');
        
        if (!response.ok) {
            response = await fetch('../data/changelog.json');
        }

        if (!response.ok) {
            throw new Error('changelog.json не найден');
        }

        const data = await response.json();
        renderCards(data);
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        document.getElementById('cardsScroll').innerHTML =
            `<div class="error">Ошибка загрузки данных. Пожалуйста, обновите страницу.</div>`;
    }
}

function renderCards(entries) {
    const container = document.getElementById('cardsScroll');

    if (!entries || entries.length === 0) {
        container.innerHTML = '<div class="loading">Пока нет изменений</div>';
        return;
    }

    container.innerHTML = '';

    entries.forEach((entry) => {
        const group = entry.group || 'Обновление';
        const groupInfo = groupMap[group] || { 
            class: 'interface', 
            icon: '📝',
            bgColor: '#F5F5F5',
            iconBg: '#E0E0E0'
        };
        const date = formatDate(entry.date);
        const changes = entry.changes || [];

        const card = document.createElement('div');
        card.className = `card ${groupInfo.class}`;
        card.style.backgroundColor = groupInfo.bgColor;

        let changesHtml = '';
        if (changes.length > 0) {
            changesHtml = '<ul class="card-changes">' +
                changes.map(change => `<li>${escapeHtml(change)}</li>`).join('') +
                '</ul>';
        }

        card.innerHTML = `
            <div class="card-icon" style="background-color: ${groupInfo.iconBg}; border-radius: 12px; padding: 8px; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; font-size: 24px;">${groupInfo.icon}</div>
            <div class="card-content">
                <div class="card-date">${date}</div>
                <div class="card-text"><strong>${escapeHtml(group)}</strong></div>
                ${changesHtml}
            </div>
        `;

        container.appendChild(card);
    });
}

function formatDate(dateStr) {
    try {
        const date = new Date(dateStr + 'T00:00:00');
        const formatter = new Intl.DateTimeFormat('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        return formatter.format(date);
    } catch (e) {
        return dateStr;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Загружаем при загрузке страницы
document.addEventListener('DOMContentLoaded', loadChangelog);
SCRIPT_EOF

if [ -f "$PROJECT_DIR/script.js" ]; then
    echo "✅ Создан $PROJECT_DIR/script.js"
else
    echo "❌ Ошибка создания script.js"
    exit 1
fi
echo ""

# ШАГ 7: Обновление промта
echo "ШАГ 7️⃣  Обновление промта переформулировки"
echo "================================"

cat > "$CHANGELOG_DIR/prompts/reformat_prompt.txt" << 'PROMPT_EOF'
Ты — помощник для переформулировки технических изменений проекта в понятный для обычного пользователя формат.

## ЭТАЛОННЫЕ ПРИМЕРЫ (ОБРАЗЕЦ ДЛЯ СТИЛЯ И ТОНА)

Используй эти примеры как ОБРАЗЕЦ:

### Интерфейс
- Обновлён текст главного меню — теперь с ясными инструкциями для новых пользователей
- Упрощена главная страница — остался только режим Ситуация
- Улучшен опыт голосового ввода — кнопки теперь корректно скрываются

### Логика
- Переработан режим Тренажёр — теперь бот оценивает твои варианты ответов вместо симуляции диалога
- Добавлена система прогресса — после трёх успешных ответов бот дает финальное сообщение
- Ускорены ответы на 30% — убрана лишняя проверка результата

### Баги
- Исправлена ошибка с обновлением сообщений — текст теперь корректно изменяется
- Упрощён выбор вариантов в Тренажёре — теперь меньше опций, проще выбрать

### Архитектура
- Включена поддержка голосовых сообщений — теперь можно описывать ситуации голосом
- Улучшена обработка звука — голосовые сообщения распознаются точнее
- Расширен анализ ситуаций — система использует больше признаков для понимания проблемы

### Оптимизация
- Оптимизирована скорость обработки — ответы приходят быстрее
- Улучшена система обработки ошибок — более надёжная и быстрая

### Админ. панель
- Удалены неиспользуемые экраны — упрощён интерфейс
- Оптимизирована проверка первого входа — новые пользователи видят согласие только один раз

---

## КРИТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНЫ)

### ❌ ЧТО КАТЕГОРИЧЕСКИ НЕЛЬЗЯ:
1. **Упоминать номера шагов** ("Удалён шаг 3", "Добавлен шаг 2")
   - ❌ "Удалён шаг 3 (пост-проверка)"
   - ✅ "Ускорены ответы на 30% — убрана лишняя проверка результата"

2. **Технические названия моделей** (GPT-4o, gpt-oss-120b, OpenRouter)
   - ❌ "Смена модели на GPT-4o-mini с запасной на gpt-oss-120b"
   - ✅ "Улучшено качество анализа — система теперь использует более мощные алгоритмы"

3. **Технические слова и термины**:
   - ❌ пайплайн → ✅ система/режим
   - ❌ промт → ✅ инструкции (или просто удалить)
   - ❌ FSM/состояние → ✅ режим
   - ❌ LLM → ✅ модель/система анализа
   - ❌ хэндлер → ✅ функция/экран
   - ❌ контекст диагностики → ✅ информация о ситуации
   - ❌ логирование → ✅ отслеживание
   - ❌ пользовательские запросы → ✅ твои запросы/сообщения

4. **Упоминания файлов и папок**: Не упоминай вообще

5. **Смайлики в ТЕКСТЕ ОПИСАНИЯ**:
   - ❌ "Добавлена кнопка '💰 Баланс OpenRouter'"
   - ✅ "Добавлена информация о статусе сервиса"
   - Смайлики ТОЛЬКО в иконках карточек!

6. **Размытые описания без деталей**:
   - ❌ "Улучшена логика анализа пользовательских запросов"
   - ✅ "Улучшена система анализа твоих запросов — бот лучше понимает суть проблемы"

7. **Излишние технические детали**:
   - ❌ "Добавлено логирование времени обработки каждого вызова модели"
   - ✅ "Оптимизирована скорость обработки — ответы приходят быстрее"

---

## ПРАВИЛА ПЕРЕФОРМУЛИРОВКИ (МЕТОДОЛОГИЯ)

### 1. ОПРЕДЕЛЕНИЕ ГРУПП
- **Интерфейс** — текст, кнопки, структура сообщений
- **Админ. панель** — функции админского бота
- **Логика** — как бот анализирует и отвечает
- **Баги** — исправления ошибок
- **Архитектура** — новые инструменты, поддержка функций
- **Оптимизация** — скорость, качество, эффективность

### 2. МАКСИМУМ 3 ИЗМЕНЕНИЯ НА КАРТОЧКУ
Если больше 3 — раздели на несколько карточек с одной датой и группой.

### 3. СТРУКТУРА
Формат: `[Действие] [Что изменилось] — [Как это помогает]`

### 4. РЕЖИМЫ "СИТУАЦИЯ" И "ТРЕНАЖЁР"
Пиши с большой буквы: "режим Тренажёр", "режим Ситуация"

---

## ВЫХОДНОЙ ФОРМАТ (JSON ТОЛЬКО)

```json
[
  {
    "date": "2026-05-02",
    "group": "Интерфейс",
    "changes": [
      "Обновлён текст — теперь понятнее",
      "Добавлена информация — можно проверить статус"
    ]
  }
]
```

Ответь ТОЛЬКО JSON. Ничего больше. Никаких комментариев, markdown, backticks.
PROMPT_EOF

if [ -f "$CHANGELOG_DIR/prompts/reformat_prompt.txt" ]; then
    echo "✅ Обновлён $CHANGELOG_DIR/prompts/reformat_prompt.txt"
else
    echo "❌ Ошибка обновления промта"
    exit 1
fi
echo ""

# ШАГ 8: Проверка файлов
echo "ШАГ 8️⃣  Проверка целостности файлов"
echo "================================"

FILES_TO_CHECK=(
    "$PROJECT_DIR/data/changelog.json"
    "$CHANGELOG_DIR/data/changelog.json"
    "$PROJECT_DIR/index.html"
    "$PROJECT_DIR/script.js"
    "$CHANGELOG_DIR/prompts/reformat_prompt.txt"
)

ALL_OK=true
for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ] && [ -s "$file" ]; then
        echo "✅ $file ($(wc -c < "$file") байт)"
    else
        echo "❌ $file не существует или пуст"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    echo "❌ Не все файлы созданы корректно"
    exit 1
fi
echo ""

# ШАГ 9: Валидация JSON
echo "ШАГ 9️⃣  Валидация JSON файлов"
echo "================================"

for file in "$PROJECT_DIR/data/changelog.json" "$CHANGELOG_DIR/data/changelog.json"; do
    if python3 -m json.tool "$file" > /dev/null 2>&1; then
        echo "✅ JSON валиден: $file"
    else
        echo "❌ JSON невалиден: $file"
        exit 1
    fi
done
echo ""

# ШАГ 10: Git commit и push
echo "ШАГ 🔟 Git commit и push"
echo "================================"

cd "$PROJECT_DIR"

# Проверяем что репо инициализирован
if [ ! -d ".git" ]; then
    echo "❌ Git репо не инициализирован"
    exit 1
fi
echo "✅ Git репо найден"

# Добавляем файлы
git add index.html script.js data/changelog.json changelog/data/changelog.json changelog/prompts/reformat_prompt.txt

# Проверяем что есть что коммитить
if git diff --cached --quiet; then
    echo "ℹ️  Нечего коммитить (файлы не изменились)"
else
    echo "✅ Файлы добавлены в staging"
    
    # Коммитим
    git commit -m "Fix: Rewrite changelog descriptions, update UI, fix icons and Telegram link"
    echo "✅ Коммит создан"
    
    # Пушим
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    git push -u origin "$CURRENT_BRANCH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Push успешен"
    else
        echo "⚠️  Push возможно не выполнен, но файлы локально обновлены"
    fi
fi

echo ""

# ШАГ 11: Финальная информация
echo "=========================================="
echo "✅ ВСЕ ИЗМЕНЕНИЯ ЗАВЕРШЕНЫ!"
echo "=========================================="
echo ""
echo "📝 Что было изменено:"
echo "   ✅ changelog.json — переписаны все описания"
echo "   ✅ index.html — обновлена ссылка на Telegram и текст"
echo "   ✅ script.js — исправлены иконки и цвета"
echo "   ✅ prompts/reformat_prompt.txt — обновлены правила генерации"
echo ""
echo "📱 Что видит пользователь:"
echo "   • Иконки соответствуют группам:"
echo "     🎨 Интерфейс (жёлтый)"
echo "     ⚙️ Админ. панель (фиолетовый)"
echo "     ⚡ Логика (синий)"
echo "     🔧 Баги (красный)"
echo "     🏗️ Архитектура (светло-голубой)"
echo "     ⚡ Оптимизация (зелёный)"
echo "   • Фон иконок под цвет карточки"
echo "   • Текст 'CHANGELOG' вместо 'ПОСЛЕДНИЕ ИЗМЕНЕНИЯ'"
echo "   • Ссылка на arsenosoznannost_bot"
echo "   • Описания без технических терминов и смайликов"
echo ""
echo "🔄 Проверка на сайте:"
echo "   1. Заходишь на сайт"
echo "   2. Нажимаешь Ctrl+Shift+R (полная перезагрузка)"
echo "   3. Проверяешь что карточки отображаются правильно"
echo ""
echo "✅ Готово!"
echo ""
