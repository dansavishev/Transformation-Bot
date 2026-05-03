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
        // Пытаемся несколько путей с cache-busting
        // Используем changelog-api папку чтобы избежать кеша GitHub Pages
        let response = await fetch(`./changelog-api/current.json?t=${Date.now()}`);

        if (!response.ok) {
            response = await fetch(`../changelog-api/current.json?t=${Date.now()}`);
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
