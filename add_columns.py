# add_columns.py
from app.database.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE user_links ADD COLUMN selected_course_id INTEGER DEFAULT 0"))
        conn.commit()
        print("✅ Колонка selected_course_id добавлена")
except Exception as e:
    print(f"Ошибка или колонка уже существует: {e}")

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE user_links ADD COLUMN selected_course_name VARCHAR(200) DEFAULT ''"))
        conn.commit()
        print("✅ Колонка selected_course_name добавлена")
except Exception as e:
    print(f"Ошибка или колонка уже существует: {e}")