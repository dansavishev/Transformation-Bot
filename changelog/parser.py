"""
Парсит отредактированный текст из админ-бота обратно в JSON
"""
import re


def parse_user_input(text):
    """
    Парсит текст в формате:
    📅 2026-05-02 | Интерфейс
    • Изменение 1
    • Изменение 2

    Возвращает список {date, group, changes}
    """
    result = []
    lines = text.split('\n')
    current_date = None
    current_group = None
    current_changes = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Строка заголовка блока: дата | группа (с эмодзи 📅 или без)
        header_match = re.match(r'(?:📅\s*)?(\d{4}-\d{2}-\d{2})\s*\|\s*(.+)', line)
        if header_match:
            # Сохраняем предыдущий блок
            if current_date and current_group and current_changes:
                result.append({
                    "date": current_date,
                    "group": current_group,
                    "changes": current_changes
                })
            current_date = header_match.group(1)
            current_group = header_match.group(2).strip()
            current_changes = []
            continue

        # Строка изменения: начинается с • или -
        if current_date and line.startswith(('•', '-')):
            current_changes.append(line[1:].strip())
        elif current_date and current_group and line:
            current_changes.append(line)

    # Последний блок
    if current_date and current_group and current_changes:
        result.append({
            "date": current_date,
            "group": current_group,
            "changes": current_changes
        })

    return result


def validate_parsed(parsed_list):
    """Проверяет что все записи имеют нужные поля"""
    if not parsed_list:
        return False
    for item in parsed_list:
        if not all(k in item for k in ['date', 'group', 'changes']):
            return False
        if not isinstance(item['changes'], list) or len(item['changes']) == 0:
            return False
    return True
