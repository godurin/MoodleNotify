from app.moodle.client import MoodleClient
from datetime import datetime, timedelta

client = MoodleClient()
_cache = {}

def get_user_courses_and_grades(moodle_user_id):
    """Автоматически получить ВСЕ курсы и оценки студента"""
    
    cache_key = f"user_{moodle_user_id}"
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=300):
            print(f"   📦 КЭШ: данные пользователя {moodle_user_id}")
            return data
    
    print(f"   🔄 ЗАГРУЗКА: получаю курсы и оценки для студента {moodle_user_id}")
    
    try:
        courses_data = client.call("core_enrol_get_users_courses", {"userid": moodle_user_id})
        
        if "errorcode" in courses_data:
            print(f"   ❌ Ошибка: {courses_data.get('message')}")
            return {}
        
        result = {}
        
        for course in courses_data:
            course_id = course.get("id")
            course_name = course.get("fullname", "")
            
            if course_name == "Moodle Local":
                continue
            
            grades_data = client.call("gradereport_user_get_grade_items", {
                "courseid": course_id,
                "userid": moodle_user_id
            })
            
            grades = []
            if "errorcode" not in grades_data:
                usergrades = grades_data.get("usergrades", [])
                if usergrades:
                    gradeitems = usergrades[0].get("gradeitems", [])
                    for item in gradeitems:
                        itemname = item.get("itemname")
                        if not itemname or itemname == ".":
                            continue
                        graderaw = item.get("graderaw")
                        if graderaw is not None:
                            grademax = item.get("grademax", 100)
                            grades.append({
                                "name": itemname,
                                "grade": graderaw,
                                "max": grademax,
                                "percent": round(graderaw / grademax * 100, 1) if grademax > 0 else 0
                            })
            
            result[course_name] = {
                "id": course_id,
                "grades": grades,
                "average": sum([g["grade"] for g in grades]) / len(grades) if grades else 0
            }
            print(f"   ✅ {course_name}: {len(grades)} оценок")
        
        _cache[cache_key] = (result, datetime.now())
        return result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {}

def clear_user_cache(moodle_user_id):
    cache_key = f"user_{moodle_user_id}"
    if cache_key in _cache:
        del _cache[cache_key]
        print(f"   🗑️ Кэш очищен")

# Для совместимости
def get_course_grades(moodle_user_id, course_id):
    data = get_user_courses_and_grades(moodle_user_id)
    for course_name, info in data.items():
        if info["id"] == course_id:
            return info["grades"]
    return []

def get_course_deadlines(moodle_user_id, course_id):
    return []