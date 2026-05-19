from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    MOODLE_URL = os.getenv("MOODLE_URL")
    MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
    VK_TOKEN = os.getenv("VK_TOKEN")
    VK_GROUP_ID = os.getenv("VK_GROUP_ID")
    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", 10))
    HIGH_RISK_THRESHOLD = float(os.getenv("HIGH_RISK_THRESHOLD", 40.0))
    MEDIUM_RISK_THRESHOLD = float(os.getenv("MEDIUM_RISK_THRESHOLD", 60.0))
    MOODLE_COURSE_ID = int(os.getenv("MOODLE_COURSE_ID", 2))
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # ========== НАСТРОЙКА БАЗЫ ДАННЫХ ==========
    _DB_URL = os.getenv("DATABASE_URL")
    
    # Если есть DATABASE_URL из переменных (например, от Railway), берем её.
    # Railway отдает ссылку как postgres://, а нам нужно postgresql:// для SQLAlchemy
    if _DB_URL and _DB_URL.startswith("postgres://"):
        _DB_URL = _DB_URL.replace("postgres://", "postgresql://", 1)
        DATABASE_URL = _DB_URL
        print("✅ Используется PostgreSQL (продакшен)")
    elif _DB_URL:
        DATABASE_URL = _DB_URL
        print("✅ Используется внешняя БД")
    else:
        # Если нет переменной DATABASE_URL — используем локальный SQLite
        DATABASE_URL = "sqlite:///moodlenotify.db"
        print("✅ Используется SQLite (локальная БД)")

settings = Settings()

print("✅ Настройки загружены:")
print(f"   Moodle URL: {settings.MOODLE_URL}")
print(f"   Check interval: {settings.CHECK_INTERVAL_MINUTES} мин")
print(f"   High risk threshold: {settings.HIGH_RISK_THRESHOLD}")
print(f"   Medium risk threshold: {settings.MEDIUM_RISK_THRESHOLD}")
print(f"   Database: {settings.DATABASE_URL}")