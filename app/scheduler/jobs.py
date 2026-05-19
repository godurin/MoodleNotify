from apscheduler.schedulers.background import BackgroundScheduler
from app.moodle.client import MoodleClient
from app.services.notify import notify_student
from app.database.service import get_all_links
from app.config import settings
import json
import os

scheduler = BackgroundScheduler()
client = MoodleClient()
CACHE_FILE = "grades_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_user_grades_from_moodle(moodle_user_id):
    """Получить ВСЕ оценки пользователя из Moodle"""
    try:
        courses_data = client.call("core_enrol_get_users_courses", {"userid": moodle_user_id})
        
        if "errorcode" in courses_data:
            print(f"      ❌ Ошибка: {courses_data.get('message')}")
            return []
        
        all_grades = []
        
        for course in courses_data:
            course_id = course.get("id")
            course_name = course.get("fullname", "")
            
            grade_data = client.call("gradereport_user_get_grade_items", {
                "courseid": course_id,
                "userid": moodle_user_id
            })
            
            if "errorcode" not in grade_data:
                usergrades = grade_data.get("usergrades", [])
                if usergrades:
                    gradeitems = usergrades[0].get("gradeitems", [])
                    for item in gradeitems:
                        itemname = item.get("itemname")
                        graderaw = item.get("graderaw")
                        
                        if itemname and itemname != "." and graderaw is not None:
                            all_grades.append({
                                "course_name": course_name,
                                "item_name": itemname,
                                "grade": graderaw
                            })
        
        print(f"      📊 Найдено оценок: {len(all_grades)}")
        return all_grades
        
    except Exception as e:
        print(f"      ❌ Ошибка: {e}")
        return []

def check_students():
    print("\n" + "="*50)
    print("🔍 [ПЛАНИРОВЩИК] Проверка новых оценок...")
    print("="*50)
    
    all_links = get_all_links()
    
    if not all_links:
        print("   📭 Нет привязанных пользователей")
        return
    
    cache = load_cache()
    
    for link in all_links:
        print(f"\n   👤 Проверяем: {link.moodle_username}")
        
        current_grades = get_user_grades_from_moodle(link.moodle_user_id)
        
        if not current_grades:
            print(f"      📭 Нет оценок")
            continue
        
        cache_key = str(link.moodle_user_id)
        old_grades = cache.get(cache_key, [])
        
        old_dict = {g["item_name"]: g["grade"] for g in old_grades}
        
        new_grades = []
        for grade in current_grades:
            item_name = grade["item_name"]
            current_val = grade["grade"]
            course_name = grade.get("course_name", "")
            
            if item_name not in old_dict:
                new_grades.append({
                    "item_name": item_name,
                    "course_name": course_name,
                    "new_grade": current_val
                })
                print(f"      🆕 Новая оценка: {course_name} - {item_name} = {current_val}")
            elif str(old_dict[item_name]) != str(current_val):
                new_grades.append({
                    "item_name": item_name,
                    "course_name": course_name,
                    "new_grade": current_val,
                    "old_grade": old_dict[item_name]
                })
                print(f"      📝 Изменилась: {course_name} - {item_name} = {current_val} (было {old_dict[item_name]})")
        
        if new_grades:
            print(f"      🔔 Отправляем уведомление о {len(new_grades)} оценках...")
            
            success = notify_student(
                vk_user_id=link.vk_user_id,
                moodle_user_id=link.moodle_user_id,
                new_grades=new_grades
            )
            
            if success:
                print(f"      ✅ Уведомление отправлено!")
            
            cache[cache_key] = current_grades
        else:
            print(f"      ✅ Новых оценок нет")
    
    save_cache(cache)
    print("="*50 + "\n")

def start_scheduler():
    print("⏰ [ПЛАНИРОВЩИК] Запуск планировщика...")
    print(f"   Интервал проверки: {settings.CHECK_INTERVAL_MINUTES} минут")
    
    scheduler.remove_all_jobs()
    scheduler.add_job(check_students, 'interval', minutes=settings.CHECK_INTERVAL_MINUTES, id='check_students')
    scheduler.start()
    print("✅ [ПЛАНИРОВЩИК] Планировщик запущен")