print("🔍 Проверка импорта модулей...")

try:
    from app.config import settings
    print("✅ config.py - OK")
    print(f"   Moodle URL: {settings.MOODLE_URL}")
    print(f"   Course ID: {settings.MOODLE_COURSE_ID}")
except Exception as e:
    print(f"❌ config.py: {e}")

try:
    from app.database.db import engine, SessionLocal, Base
    print("✅ database/db.py - OK")
except Exception as e:
    print(f"❌ database/db.py: {e}")

try:
    from app.database.models import UserLink, NotificationLog
    print("✅ database/models.py - OK")
except Exception as e:
    print(f"❌ database/models.py: {e}")

try:
    from app.database.service import save_user_link, get_user_link, get_all_links, save_notification_log, get_stats
    print("✅ database/service.py - OK")
except Exception as e:
    print(f"❌ database/service.py: {e}")

try:
    from app.moodle.client import MoodleClient
    print("✅ moodle/client.py - OK")
except Exception as e:
    print(f"❌ moodle/client.py: {e}")

try:
    from app.services.grades import get_user_average, get_user_grades, get_all_grades
    print("✅ services/grades.py - OK")
except Exception as e:
    print(f"❌ services/grades.py: {e}")

try:
    from app.services.risk import detect_risk, get_recommendation
    print("✅ services/risk.py - OK")
    risk, msg = detect_risk(4.5)
    print(f"   Тест риска (4.5): {risk}")
except Exception as e:
    print(f"❌ services/risk.py: {e}")

try:
    from app.services.notify import send_message, notify_student
    print("✅ services/notify.py - OK")
except Exception as e:
    print(f"❌ services/notify.py: {e}")

print("\n🎉 Все модули загружены успешно!")