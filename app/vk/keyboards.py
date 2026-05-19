import json

def main_keyboard():
    """Главное меню с кнопками"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "🔗 Привязать Moodle"}, "color": "primary"}
            ],
            [
                {"action": {"type": "text", "label": "📊 Моя успеваемость"}, "color": "positive"}
            ],
            [
                {"action": {"type": "text", "label": "🔮 Прогноз"}, "color": "primary"},
                {"action": {"type": "text", "label": "⚠️ Дедлайны"}, "color": "secondary"}
            ],
            [
                {"action": {"type": "text", "label": "⚙️ Настройки"}, "color": "default"},
                {"action": {"type": "text", "label": "🔄 Обновить данные"}, "color": "default"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def settings_keyboard():
    """Клавиатура для настроек"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "🔔 Включить уведомления"}, "color": "positive"},
                {"action": {"type": "text", "label": "🔕 Выключить уведомления"}, "color": "negative"}
            ],
            [
                {"action": {"type": "text", "label": "◀️ Главное меню"}, "color": "default"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def back_keyboard():
    """Клавиатура с кнопкой 'Назад'"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [{"action": {"type": "text", "label": "◀️ Главное меню"}, "color": "default"}]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def courses_keyboard(courses):
    """Клавиатура для выбора дисциплины (динамическая)"""
    buttons = []
    for course_id, course_name in courses[:6]:
        buttons.append([{"action": {"type": "text", "label": course_name[:35]}, "color": "primary"}])
    buttons.append([{"action": {"type": "text", "label": "◀️ Назад"}, "color": "default"}])
    
    keyboard = {"one_time": False, "buttons": buttons}
    return json.dumps(keyboard, ensure_ascii=False)