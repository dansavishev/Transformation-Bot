// Маппинг групп на CSS классы и иконки
const groupMap = {
    'Интерфейс': { class: 'interface', icon: '✨' },
    'Админ. панель': { class: 'admin', icon: '⚙️' },
    'Логика': { class: 'logic', icon: '🧠' },
    'Баги': { class: 'bug', icon: '🐞' },
    'Архитектура': { class: 'architecture', icon: '🧱' },
    'Оптимизация': { class: 'optimization', icon: '⚡' }
};

async function loadChangelog() {
    try {
        // Пытаемся несколько путей
        let response = await fetch('/changelog/data/changelog.json');
        
        if (!response.ok) {
            response = await fetch('./data/changelog.json');
        }
        
        if (!response.ok) {
            response = await fetch('../data/changelog.json');
        }

        if (!response.ok) {
            throw new Error('changelog.json не найден ни по одному пути');
        }

        const data = await response.json();
        renderCards(data);
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        document.getElementById('cardsScroll').innerHTML =
            `<div class="error">❌ Ошибка загрузки: ${error.message}</div>`;
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
        const groupInfo = groupMap[group] || { class: 'interface', icon: '📝' };
        const date = formatDate(entry.date);
        const changes = entry.changes || [];

        const card = document.createElement('div');
        card.className = `card ${groupInfo.class}`;

        let changesHtml = '';
        if (changes.length > 0) {
            changesHtml = '<ul class="card-changes">' +
                changes.map(change => `<li>${escapeHtml(change)}</li>`).join('') +
                '</ul>';
        }

        card.innerHTML = `
            <div class="card-icon">${groupInfo.icon}</div>
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
