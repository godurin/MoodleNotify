from app.database.service import save_user_link, get_user_link, get_all_links, get_stats

print("💾 Проверка работы с базой данных")

# Тест 1: Сохранить пользователя
print("\n1. Сохранение пользователя...")
result = save_user_link(
    vk_user_id=123456789,
    moodle_user_id=100,
    moodle_username="test_student",
    moodle_fullname="Тестовый Студент"
)
print(f"   Результат: {'✅ успешно' if result else '❌ ошибка'}")

# Тест 2: Получить пользователя
print("\n2. Получение пользователя...")
user = get_user_link(123456789)
if user:
    print(f"   ✅ Найден: {user.moodle_fullname} (VK ID: {user.vk_user_id})")
else:
    print("   ❌ Не найден")

# Тест 3: Получить всех пользователей
print("\n3. Получение всех пользователей...")
all_users = get_all_links()
print(f"   Всего пользователей: {len(all_users)}")

# Тест 4: Получить статистику
print("\n4. Получение статистики...")
stats = get_stats()
print(f"   Всего пользователей: {stats['total_users']}")
print(f"   Всего уведомлений: {stats['total_notifications']}")
print(f"   В группе риска: {stats['high_risk_users']}")

print("\n✨ Проверка БД завершена")