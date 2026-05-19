from app.config import settings
from app.moodle.client import MoodleClient

print("🔌 Проверка подключения к Moodle")
print(f"URL: {settings.MOODLE_URL}")
print(f"Token: {settings.MOODLE_TOKEN[:10]}... (скрыто)")

client = MoodleClient()

# Проверка 1: Получить информацию о сайте
try:
    print("\n1. Проверка API - получение информации о сайте...")
    site_info = client.call("core_webservice_get_site_info")
    if "errorcode" in site_info:
        print(f"❌ Ошибка: {site_info.get('message', 'Неизвестная ошибка')}")
    else:
        print(f"✅ Сайт: {site_info.get('sitename', 'Неизвестно')}")
        print(f"   Версия Moodle: {site_info.get('release', 'Неизвестно')}")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")

# Проверка 2: Получить пользователей курса (если есть курс с ID=2)
print("\n2. Проверка получения пользователей курса...")
try:
    users = client.call(
        "core_enrol_get_enrolled_users",
        {"courseid": settings.MOODLE_COURSE_ID}
    )
    if "errorcode" in users:
        print(f"❌ Ошибка: {users.get('message', 'Неизвестная ошибка')}")
    else:
        print(f"✅ Найдено пользователей: {len(users)}")
        if users:
            print(f"   Пример: {users[0].get('fullname', 'Без имени')} (ID: {users[0].get('id')})")
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n✨ Проверка завершена")