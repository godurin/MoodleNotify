from vk_api.longpoll import VkLongPoll, VkEventType
from app.services.vk import vk_session, send_message
from app.vk.keyboards import main_keyboard, settings_keyboard, back_keyboard, courses_keyboard
from app.services.moodle_users import find_user_by_username
from app.services.courses import get_user_courses_and_grades, clear_user_cache
from app.database.service import save_user_link, get_user_link, update_notification_settings, get_user_courses, update_selected_course
from app.config import settings
from app.services.risk import detect_risk
from app.moodle.client import MoodleClient
import json
from datetime import datetime

longpoll = VkLongPoll(vk_session)
waiting_for_link = {}
waiting_for_course = {}

def safe_send(user_id, message, keyboard=None):
    try:
        return send_message(user_id, message, keyboard)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def get_detailed_performance(moodle_user_id):
    """Получить все оценки по всем дисциплинам + итоговую сумму по каждой"""
    data = get_user_courses_and_grades(moodle_user_id)
    
    if not data:
        return "📭 Нет данных об успеваемости"
    
    msg = "📊 **ВСЕ ОЦЕНКИ**\n\n"
    
    for course_name, info in data.items():
        msg += f"📖 **{course_name}**\n"
        if info["grades"]:
            total_sum = 0
            for g in info["grades"]:
                msg += f"   • {g['name']}: {g['grade']} / {g['max']} ({g['percent']}%)\n"
                total_sum += g['grade']
            msg += f"\n   💰 **Итого баллов:** {total_sum}\n\n"
        else:
            msg += "   📭 Оценок пока нет\n\n"
    
    return msg

def get_course_grades(moodle_user_id, course_name):
    """Получить ВСЕ оценки по конкретной дисциплине + итоговую сумму"""
    data = get_user_courses_and_grades(moodle_user_id)
    
    for name, info in data.items():
        if name == course_name:
            if not info["grades"]:
                return f"📖 **{name}**\n\n📭 Оценок пока нет"
            
            msg = f"📖 **{name}**\n\n"
            msg += "📊 **ВСЕ ОЦЕНКИ:**\n\n"
            
            total_sum = 0
            for g in info["grades"]:
                msg += f"   • {g['name']}: {g['grade']} / {g['max']} ({g['percent']}%)\n"
                total_sum += g['grade']
            
            # Добавляем итоговую сумму баллов
            msg += f"\n📊 **ИТОГО БАЛЛОВ:** {total_sum}"
            
            return msg
    
    return f"❌ Дисциплина '{course_name}' не найдена"

def get_forecast(moodle_user_id):
    """Получить прогноз успеваемости (100-балльная система)"""
    data = get_user_courses_and_grades(moodle_user_id)
    
    if not data:
        return "📭 Нет данных для прогноза"
    
    msg = "🔮 **ПРОГНОЗ УСПЕВАЕМОСТИ**\n\n"
    
    for course_name, info in data.items():
        if info["grades"]:
            total_score = sum([g['grade'] for g in info['grades']])
            avg_score = total_score / len(info['grades'])
            
            if avg_score >= 80:
                prediction = "🎯 Отлично! Так держать!"
                advice = "Продолжайте в том же духе"
            elif avg_score >= 60:
                prediction = "📈 Хорошо, но есть куда расти"
                advice = "Поставьте цель подняться до 80 баллов"
            elif avg_score >= 40:
                prediction = "⚠️ Нужно подтянуть знания"
                advice = "Обратитесь к преподавателю за консультацией"
            else:
                prediction = "🔴 Критическая ситуация!"
                advice = "Срочно свяжитесь с преподавателем!"
            
            msg += f"📖 **{course_name}**\n"
            msg += f"   📊 Текущий балл: {avg_score:.1f}/100\n"
            msg += f"   {prediction}\n"
            msg += f"   💡 {advice}\n\n"
        else:
            msg += f"📖 **{course_name}**\n"
            msg += f"   📭 Нет оценок для прогноза\n\n"
    
    return msg

def get_deadlines(moodle_user_id):
    """Получить ближайшие дедлайны из Moodle"""
    client = MoodleClient()
    
    try:
        # Получаем список курсов пользователя
        courses_data = client.call("core_enrol_get_users_courses", {"userid": moodle_user_id})
        
        if "errorcode" in courses_data:
            return "⏰ Не удалось получить дедлайны"
        
        deadlines = []
        
        for course in courses_data:
            course_id = course.get("id")
            course_name = course.get("fullname", "")
            
            # Получаем задания курса
            assignments_data = client.call("mod_assign_get_assignments", {"courseids": [course_id]})
            
            if "errorcode" not in assignments_data:
                for c in assignments_data.get("courses", []):
                    for assignment in c.get("assignments", []):
                        deadline = assignment.get("duedate", 0)
                        if deadline > 0:
                            deadline_date = datetime.fromtimestamp(deadline)
                            now = datetime.now()
                            
                            if deadline_date > now:
                                days_left = (deadline_date - now).days
                                hours_left = (deadline_date - now).seconds // 3600
                                
                                if days_left == 0:
                                    time_left = f"{hours_left} часов"
                                elif days_left == 1:
                                    time_left = "1 день"
                                else:
                                    time_left = f"{days_left} дней"
                                
                                deadlines.append({
                                    "course_name": course_name,
                                    "assignment_name": assignment.get("name", "Без названия"),
                                    "deadline": deadline_date,
                                    "time_left": time_left
                                })
        
        if not deadlines:
            return "✅ Нет ближайших дедлайнов!\n\nВсе задания сданы вовремя."
        
        # Сортируем по дате
        deadlines.sort(key=lambda x: x["deadline"])
        
        msg = "⏰ **БЛИЖАЙШИЕ ДЕДЛАЙНЫ**\n\n"
        for d in deadlines[:10]:
            msg += f"📖 **{d['course_name']}**\n"
            msg += f"   📝 {d['assignment_name']}\n"
            msg += f"   ⏳ Осталось: {d['time_left']}\n"
            msg += f"   📅 До {d['deadline'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        return msg
    except Exception as e:
        print(f"❌ Ошибка получения дедлайнов: {e}")
        return "⏰ Функция дедлайнов временно недоступна"

def run_bot():
    print("🤖 VK BOT STARTED")
    print("👂 Ожидание сообщений...")
    
    for event in longpoll.listen():
        if event.type != VkEventType.MESSAGE_NEW:
            continue
        if not event.to_me:
            continue
        
        user_id = event.user_id
        text = event.text.strip()
        print(f"📨 От {user_id}: {text}")
        
        # ========== ОБРАБОТКА ПРИВЯЗКИ АККАУНТА ==========
        if waiting_for_link.get(user_id):
            user = find_user_by_username(text)
            if user:
                save_user_link(user_id, user["id"], user["username"], user.get("fullname"))
                safe_send(user_id, f"✅ Аккаунт привязан!\n👤 {user.get('fullname')}", main_keyboard())
                
                data = get_user_courses_and_grades(user["id"])
                if data:
                    msg = get_detailed_performance(user["id"])
                    safe_send(user_id, msg, main_keyboard())
                else:
                    safe_send(user_id, "📭 У вас нет дисциплин в Moodle", main_keyboard())
            else:
                safe_send(user_id, f"❌ Пользователь '{text}' не найден", main_keyboard())
            waiting_for_link[user_id] = False
            continue
        
        # ========== ОБРАБОТКА ВЫБОРА ДИСЦИПЛИНЫ ==========
        if waiting_for_course.get(user_id):
            link = get_user_link(user_id)
            if link:
                courses = get_user_courses(user_id)
                selected_course = None
                
                for course_id, course_name in courses:
                    if text == course_name or text in course_name or course_name in text:
                        selected_course = (course_id, course_name)
                        break
                
                if selected_course:
                    course_id, course_name = selected_course
                    
                    # Показываем оценки по выбранной дисциплине
                    msg = get_course_grades(link.moodle_user_id, course_name)
                    safe_send(user_id, msg, main_keyboard())
                else:
                    safe_send(user_id, f"❌ Дисциплина не найдена.\n\nВы написали: '{text}'", main_keyboard())
                
                waiting_for_course[user_id] = False
                continue
            waiting_for_course[user_id] = False
            continue
        
        # ========== ОБРАБОТКА КОМАНД ==========
        if text.lower() in ["начать", "меню", "главное меню", "◀️ главное меню"]:
            safe_send(user_id, "🌟 **Главное меню**\n\nВыберите действие:", main_keyboard())
        
        elif text == "🔗 Привязать Moodle" or text == "🔗 Привязать Moodle":
            waiting_for_link[user_id] = True
            safe_send(user_id, "🔗 Введите ваш логин из Moodle:", back_keyboard())

        elif text == "🔗 Привязать Moodle":
            waiting_for_link[user_id] = True
            safe_send(user_id, "🔗 Введите ваш логин из Moodle:", back_keyboard())
        
        elif text == "📊 Моя успеваемость":
            link = get_user_link(user_id)
            if not link:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!\n\nНажмите '🔗 Привязать Moodle'", main_keyboard())
                continue
            
            # Получаем список дисциплин
            courses = get_user_courses(user_id)
            if not courses:
                safe_send(user_id, "📭 У вас нет дисциплин в Moodle\n\nНажмите 'Обновить данные'", main_keyboard())
                continue
            
            # Сохраняем состояние - ожидаем выбора дисциплины
            waiting_for_course[user_id] = True
            
            # Показываем клавиатуру с предметами
            buttons = []
            for course_id, course_name in courses[:6]:
                buttons.append([{"action": {"type": "text", "label": course_name[:35]}, "color": "primary"}])
            buttons.append([{"action": {"type": "text", "label": "◀️ Назад"}, "color": "default"}])
            
            keyboard = json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)
            safe_send(user_id, "📚 **Выберите дисциплину:**", keyboard)

        elif text == "🔮 Прогноз":
            link = get_user_link(user_id)
            if not link:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!\n\nНапишите '🔗 Привязать Moodle'", main_keyboard())
                continue
            
            msg = get_forecast(link.moodle_user_id)
            safe_send(user_id, msg, main_keyboard())
        
        elif text == "⚠️ Дедлайны":
            link = get_user_link(user_id)
            if not link:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!", main_keyboard())
                continue
            
            msg = get_deadlines(link.moodle_user_id)
            safe_send(user_id, msg, main_keyboard())
        
        elif text == "⚙️ Настройки":
            link = get_user_link(user_id)
            if not link:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!", main_keyboard())
                continue
            
            settings_msg = f"⚙️ **НАСТРОЙКИ**\n\n👤 Пользователь: {link.moodle_username}\n📊 Текущий балл: {link.last_notification_grade or 'нет данных'}\n🔔 Уведомления: {'Включены' if link.notification_type != 'none' else 'Выключены'}\n\nВыберите действие:"
            safe_send(user_id, settings_msg, settings_keyboard())
        
        elif text == "🔔 Включить уведомления":
            update_notification_settings(user_id, "all")
            safe_send(user_id, "🔔 Уведомления **включены**!\n\nВы будете получать отчёты об успеваемости.", settings_keyboard())
        
        elif text == "🔕 Выключить уведомления":
            update_notification_settings(user_id, "none")
            safe_send(user_id, "🔕 Уведомления **выключены**!\n\nВы не будете получать автоматические отчёты.", settings_keyboard())
        
        elif text == "📋 Выбрать дисциплину":
            courses = get_user_courses(user_id)
            if not courses:
                safe_send(user_id, "📭 У вас нет дисциплин в Moodle\n\nНажмите 'Обновить данные'", settings_keyboard())
                continue
            
            waiting_for_course[user_id] = True
            
            buttons = []
            for course_id, course_name in courses[:6]:
                buttons.append([{"action": {"type": "text", "label": course_name[:35]}, "color": "primary"}])
            buttons.append([{"action": {"type": "text", "label": "◀️ Назад"}, "color": "default"}])
            
            keyboard = json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)
            safe_send(user_id, "📚 **Выберите дисциплину**\n\nНажмите на нужный предмет, чтобы увидеть все оценки:", keyboard)
        
        elif text == "🔄 Обновить данные":
            link = get_user_link(user_id)
            if link:
                clear_user_cache(link.moodle_user_id)
                safe_send(user_id, "✅ Данные обновлены!\n\nНажмите 'Моя успеваемость' для просмотра", main_keyboard())
            else:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!", main_keyboard())
        
        elif text == "◀️ Назад":
            safe_send(user_id, "🌟 Главное меню", main_keyboard())
        
        elif text == "Мои оценки":
            link = get_user_link(user_id)
            if not link:
                safe_send(user_id, "⚠️ Сначала привяжите аккаунт!", main_keyboard())
                continue
            
            msg = get_detailed_performance(link.moodle_user_id)
            safe_send(user_id, msg, main_keyboard())
        
        else:
            safe_send(user_id, "🤔 Не понял команду.\n\nНапишите 'меню' для списка команд", main_keyboard())