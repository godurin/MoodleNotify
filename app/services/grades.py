from app.services.cache import cached
from app.moodle.client import MoodleClient

client = MoodleClient()

@cached(ttl=300)
def get_user_average(user_id, course_id):
    """Получить средний балл (с кэшем)"""
    grades = get_user_grades(user_id, course_id)
    values = []
    for grade in grades:
        if grade.get("grade") is not None:
            try:
                values.append(float(grade["grade"]))
            except:
                pass
    if not values:
        return 0
    return round(sum(values) / len(values), 2)

@cached(ttl=300)
def get_user_grades(user_id, course_id):
    """Получить оценки (с кэшем)"""
    data = client.call(
        "gradereport_user_get_grade_items",
        {
            "courseid": course_id,
            "userid": user_id
        }
    )
    
    usergrades = data.get("usergrades", [])
    if not usergrades:
        return []
    
    gradeitems = usergrades[0].get("gradeitems", [])
    
    result = []
    for item in gradeitems:
        itemname = item.get("itemname")
        graderaw = item.get("graderaw")
        
        if not itemname or itemname == ".":
            continue
        
        if graderaw is not None:
            result.append({
                "name": itemname,
                "grade": graderaw
            })
    
    return result

def get_all_grades(user_id, course_id):
    """Получить все оценки (без кэша - для обновлений)"""
    return get_user_grades(user_id, course_id)
from app.moodle.client import MoodleClient

client = MoodleClient()

def get_user_grade_items_count(user_id, course_id):
    """Получить общее количество заданий в курсе"""
    try:
        data = client.call(
            "gradereport_user_get_grade_items",
            {
                "courseid": course_id,
                "userid": user_id
            }
        )
        
        usergrades = data.get("usergrades", [])
        if not usergrades:
            return 0
        
        gradeitems = usergrades[0].get("gradeitems", [])
        return len(gradeitems)
    except:
        return 20  # Значение по умолчанию

# Остальные функции оставляем без изменений...
def get_user_average(user_id, course_id):
    grades = get_user_grades(user_id, course_id)
    values = []
    for grade in grades:
        if grade["grade"] is not None:
            grade_val = float(grade["grade"])
            # Если оценка до 100, переводим в 10-балльную для риска
            if grade_val > 10:
                grade_val = grade_val / 10
            values.append(grade_val)
    
    if not values:
        return 0
    average = sum(values) / len(values)
    return round(average, 2)

def get_user_grades(user_id, course_id):
    data = client.call(
        "gradereport_user_get_grade_items",
        {
            "courseid": course_id,
            "userid": user_id
        }
    )
    usergrades = data.get("usergrades", [])
    if not usergrades:
        return []
    gradeitems = usergrades[0].get("gradeitems", [])
    result = []
    for item in gradeitems:
        itemname = item.get("itemname")
        graderaw = item.get("graderaw")
        if not itemname:
            continue
        result.append({
            "name": itemname,
            "grade": graderaw
        })
    return result

def get_all_grades(user_id, course_id):
    data = client.call(
        "gradereport_user_get_grade_items",
        {
            "courseid": course_id,
            "userid": user_id
        }
    )
    usergrades = data.get("usergrades", [])
    if not usergrades:
        return []
    gradeitems = usergrades[0].get("gradeitems", [])
    results = []
    for item in gradeitems:
        itemname = item.get("itemname")
        graderaw = item.get("graderaw")
        if itemname and graderaw is not None:
            results.append({
                "name": itemname,
                "grade": graderaw
            })
    return results