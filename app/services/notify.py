import random
import vk_api
from app.config import settings
from app.database.service import save_notification_log

vk_session = vk_api.VkApi(token=settings.VK_TOKEN)
vk = vk_session.get_api()

def send_message(user_id, message, keyboard=None):
    try:
        params = {
            "user_id": user_id,
            "message": message,
            "random_id": random.randint(1, 1000000)
        }
        if keyboard:
            params["keyboard"] = keyboard
        response = vk.messages.send(**params)
        print(f"✅ VK RESPONSE: {response}")
        return True
    except Exception as e:
        print(f"❌ VK ERROR: {e}")
        return False

def get_student_risk_status(moodle_user_id):
    """Получить статус риска студента на основе его текущих оценок"""
    from app.services.courses import get_user_courses_and_grades
    
    data = get_user_courses_and_grades(moodle_user_id)
    
    if not data:
        return None, None
    
    all_grades = []
    for course_name, info in data.items():
        for g in info['grades']:
            all_grades.append(g['grade'])
    
    if not all_grades:
        return None, None
    
    avg_grade = sum(all_grades) / len(all_grades)
    
    if avg_grade < 40:
        return "HIGH_RISK", f"🔴 ВЫСОКИЙ РИСК\n💡 Нужно срочно исправлять ситуацию! Обратитесь к преподавателю."
    elif avg_grade < 60:
        return "MEDIUM_RISK", f"🟡 СРЕДНИЙ РИСК\n💡 Стоит подтянуть оценки, обратите внимание на сложные темы."
    else:
        return "LOW_RISK", f"🟢 НИЗКИЙ РИСК\n💡 Продолжайте в том же духе!"

def notify_student(vk_user_id, moodle_user_id, new_grades=None):
    """Отправить уведомление студенту о новых оценках + статус риска"""
    
    if not new_grades:
        return False

    # Формируем список новых оценок
    grades_text = "📝 **НОВЫЕ ОЦЕНКИ:**\n\n"
    for grade in new_grades[:5]:
        course = grade.get("course_name", "Неизвестный предмет")
        grades_text += f"📖 **{course}**\n"
        grades_text += f"   • {grade['item_name']}: **{grade['new_grade']}**\n\n"
    
    # Получаем статус риска
    risk_level, risk_text = get_student_risk_status(moodle_user_id)
    
    if risk_text:
        risk_section = f"\n📈 **Ваш статус:**\n{risk_text}\n"
    else:
        risk_section = "\n📈 Нет данных для определения статуса.\n"

    message = f"""📊 **ОБНОВЛЕНИЕ ОЦЕНОК**

{grades_text}
{risk_section}
---
💡 Используйте меню для просмотра всех оценок."""

    success = send_message(vk_user_id, message)

    save_notification_log(
        vk_user_id=vk_user_id,
        moodle_user_id=moodle_user_id,
        message=message,
        risk_level=risk_level,
        avg_grade=None,
        success=success
    )
    return success