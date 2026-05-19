"""
Тестирование уведомлений о новых оценках
Запуск: python test_notification_flow.py
"""

import time
from app.database.service import save_user_link, get_user_link, save_grades_to_history
from app.services.notify import notify_new_grades
from app.services.grades import get_all_grades
from app.config import settings

# === НАСТРОЙКИ ===
YOUR_VK_ID = 473570076  # ЗАМЕНИТЕ НА ВАШ VK ID

print("="*60)
print("ТЕСТИРОВАНИЕ УВЕДОМЛЕНИЙ О НОВЫХ ОЦЕНКАХ")
print("="*60)

# Шаг 1: Проверка привязки
print("\n1. Проверка привязки пользователя...")
link = get_user_link(YOUR_VK_ID)

if not link:
    print("❌ Пользователь не привязан!")
    print("   Напишите боту 'Привязать Moodle' и введите логин")
    exit()

print(f"✅ Привязан: {link.moodle_fullname} (Логин: {link.moodle_username})")

# Шаг 2: Получаем реальные оценки
print("\n2. Получение текущих оценок из Moodle...")
real_grades = get_all_grades(
    user_id=link.moodle_user_id,
    course_id=settings.MOODLE_COURSE_ID
)
print(f"   Найдено оценок: {len(real_grades)}")

# Шаг 3: Сохраняем первый раз (базовое состояние)
print("\n3. Сохраняем базовое состояние...")
save_grades_to_history(
    vk_user_id=YOUR_VK_ID,
    moodle_user_id=link.moodle_user_id,
    course_id=settings.MOODLE_COURSE_ID,
    grades=real_grades
)
print("   ✅ Базовое состояние сохранено")

# Шаг 4: Имитация новой оценки
print("\n4. Имитация получения новой оценки...")

# Создаём копию оценок с изменением
modified_grades = real_grades.copy() if real_grades else []

# Добавляем тестовую оценку
test_grade = {
    "name": "ТЕСТОВАЯ ОЦЕНКА",
    "grade": 9.0
}
modified_grades.append(test_grade)

# Шаг 5: Проверяем изменения
print("\n5. Проверка изменений...")
new_grades = save_grades_to_history(
    vk_user_id=YOUR_VK_ID,
    moodle_user_id=link.moodle_user_id,
    course_id=settings.MOODLE_COURSE_ID,
    grades=modified_grades
)

print(f"   Обнаружено изменений: {len(new_grades)}")
for g in new_grades:
    print(f"   - {g['name']}: {g['old_grade']} → {g['new_grade']}")

# Шаг 6: Отправляем уведомление
print("\n6. Отправка уведомления в VK...")
if new_grades:
    notify_new_grades(YOUR_VK_ID, new_grades)
    print("   ✅ Уведомление отправлено! Проверьте VK бота")
else:
    print("   ❌ Нет изменений для отправки")

print("\n" + "="*60)
print("Если уведомление пришло - всё работает!")
print("Если нет - проверьте VK ID и настройки")
print("="*60)