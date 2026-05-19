from app.database.db import SessionLocal
from app.database.models import UserLink, NotificationLog, Course, Grade, Deadline
from datetime import datetime


# ========== ОСНОВНЫЕ ФУНКЦИИ ==========

def save_user_link(vk_user_id, moodle_user_id, moodle_username, moodle_fullname=None):
    db = SessionLocal()
    try:
        existing = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        if existing:
            existing.moodle_user_id = moodle_user_id
            existing.moodle_username = moodle_username
            if moodle_fullname:
                existing.moodle_fullname = moodle_fullname
            existing.updated_at = datetime.utcnow()
        else:
            user = UserLink(
                vk_user_id=vk_user_id,
                moodle_user_id=moodle_user_id,
                moodle_username=moodle_username,
                moodle_fullname=moodle_fullname or moodle_username
            )
            db.add(user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка сохранения: {e}")
        return False
    finally:
        db.close()


def get_user_link(vk_user_id):
    db = SessionLocal()
    try:
        user = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        return user
    finally:
        db.close()


def get_all_links():
    db = SessionLocal()
    try:
        users = db.query(UserLink).all()
        return users
    finally:
        db.close()


def update_notification_settings(vk_user_id, notification_type):
    db = SessionLocal()
    try:
        user = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        if user:
            user.notification_type = notification_type
            db.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()
    return False


def save_notification_log(vk_user_id, moodle_user_id, message, risk_level, avg_grade, success=True, error_msg=None):
    print(f"🔍 СОХРАНЕНИЕ ЛОГА: VK={vk_user_id}, риск={risk_level}, балл={avg_grade}, успех={success}")
    db = SessionLocal()
    try:
        log = NotificationLog(
            vk_user_id=vk_user_id,
            moodle_user_id=moodle_user_id,
            message_text=message[:1000],
            risk_level=risk_level,
            avg_grade=avg_grade,
            success=1 if success else 0,
            error_message=error_msg[:500] if error_msg else None
        )
        db.add(log)
        db.commit()
        
        user = get_user_link(vk_user_id)
        if user:
            user.last_notification_grade = avg_grade
            user.last_notification_risk = risk_level
            db.commit()
        
        print(f"✅ Лог успешно сохранен! ID={log.id}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения лога: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_stats():
    db = SessionLocal()
    try:
        total_users = db.query(UserLink).count()
        total_notifications = db.query(NotificationLog).count()
        high_risk_users = db.query(UserLink).filter(
            UserLink.last_notification_risk == "HIGH_RISK"
        ).count()
        
        recent_logs = db.query(NotificationLog).order_by(
            NotificationLog.sent_at.desc()
        ).limit(10).all()
        
        return {
            "total_users": total_users,
            "total_notifications": total_notifications,
            "high_risk_users": high_risk_users,
            "recent_logs": [
                {
                    "vk_user_id": log.vk_user_id,
                    "risk_level": log.risk_level,
                    "avg_grade": log.avg_grade,
                    "sent_at": log.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log.sent_at else None,
                    "success": log.success
                } for log in recent_logs
            ]
        }
    finally:
        db.close()


# ========== ФУНКЦИИ ДЛЯ КУРСОВ И ОЦЕНОК ==========

def save_courses(moodle_user_id, courses):
    """Сохранить список курсов пользователя"""
    db = SessionLocal()
    try:
        # Удаляем старые курсы
        db.query(Course).filter(Course.moodle_user_id == moodle_user_id).delete()
        
        # Добавляем новые
        for course in courses:
            db_course = Course(
                moodle_user_id=moodle_user_id,
                course_id=course["course_id"],
                course_name=course["course_name"],
                course_shortname=course.get("course_shortname", "")
            )
            db.add(db_course)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка сохранения курсов: {e}")
        return False
    finally:
        db.close()


def get_user_courses(vk_user_id):
    """Получить курсы пользователя (сначала из БД, если нет - из Moodle)"""
    db = SessionLocal()
    try:
        user = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        if not user:
            return []
        
        courses = db.query(Course).filter(Course.moodle_user_id == user.moodle_user_id).all()
        
        # Если в БД нет курсов - получаем из Moodle и сохраняем
        if not courses:
            print(f"🔄 Курсы не найдены в БД, загружаю из Moodle для пользователя {user.moodle_user_id}")
            from app.services.courses import get_user_courses_and_grades
            
            data = get_user_courses_and_grades(user.moodle_user_id)
            if data:
                courses_to_save = []
                for course_name, info in data.items():
                    courses_to_save.append({
                        "course_id": info["id"],
                        "course_name": course_name,
                        "course_shortname": course_name
                    })
                save_courses(user.moodle_user_id, courses_to_save)
                
                # Повторно получаем из БД
                courses = db.query(Course).filter(Course.moodle_user_id == user.moodle_user_id).all()
        
        return [(c.course_id, c.course_name) for c in courses]
    finally:
        db.close()

def save_grades(moodle_user_id, course_id, grades):
    """Сохранить оценки в БД и определить новые"""
    db = SessionLocal()
    try:
        new_grades = []
        
        # Получаем старые оценки
        old_grades = db.query(Grade).filter(
            Grade.moodle_user_id == moodle_user_id,
            Grade.course_id == course_id
        ).all()
        
        old_dict = {g.item_name: g.grade_raw for g in old_grades}
        
        for grade in grades:
            existing = db.query(Grade).filter(
                Grade.moodle_user_id == moodle_user_id,
                Grade.course_id == course_id,
                Grade.item_name == grade["item_name"]
            ).first()
            
            is_new = False
            if not existing:
                is_new = True
                existing = Grade(
                    moodle_user_id=moodle_user_id,
                    course_id=course_id
                )
                db.add(existing)
            
            # Проверяем, изменилась ли оценка
            if str(existing.grade_raw) != str(grade["grade_raw"]):
                is_new = True
                new_grades.append({
                    "item_name": grade["item_name"],
                    "old_grade": existing.grade_raw or "нет",
                    "new_grade": grade["grade_raw"]
                })
            
            existing.item_name = grade["item_name"]
            existing.grade_value = grade["grade_value"]
            existing.grade_raw = str(grade["grade_raw"])
            existing.is_new = is_new
        
        db.commit()
        return new_grades
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка сохранения оценок: {e}")
        return []
    finally:
        db.close()


def update_selected_course(vk_user_id, course_id, course_name):
    """Обновить выбранную дисциплину пользователя"""
    db = SessionLocal()
    try:
        user = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        if user:
            user.selected_course_id = course_id
            user.selected_course_name = course_name
            db.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()
    return False


def save_deadlines(moodle_user_id, deadlines):
    """Сохранить дедлайны"""
    db = SessionLocal()
    try:
        for deadline in deadlines:
            existing = db.query(Deadline).filter(
                Deadline.moodle_user_id == moodle_user_id,
                Deadline.assignment_name == deadline["assignment_name"]
            ).first()
            
            if not existing:
                existing = Deadline(moodle_user_id=moodle_user_id)
                db.add(existing)
            
            existing.course_id = deadline.get("course_id", 0)
            existing.course_name = deadline.get("course_name", "")
            existing.assignment_name = deadline["assignment_name"]
            existing.deadline = deadline["deadline"]
            existing.description = deadline.get("description", "")
        
        db.commit()
    except Exception as e:
        print(f"❌ Ошибка сохранения дедлайнов: {e}")
        db.rollback()
    finally:
        db.close()


def get_upcoming_deadlines(vk_user_id, days=7):
    """Получить дедлайны на ближайшие N дней"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        user = db.query(UserLink).filter(UserLink.vk_user_id == vk_user_id).first()
        if not user:
            return []
        
        now = datetime.utcnow()
        week_later = now + timedelta(days=days)
        
        deadlines = db.query(Deadline).filter(
            Deadline.moodle_user_id == user.moodle_user_id,
            Deadline.deadline > now,
            Deadline.deadline < week_later
        ).order_by(Deadline.deadline).all()
        
        return deadlines
    finally:
        db.close()


def mark_deadline_notified(moodle_user_id, assignment_name):
    """Отметить, что уведомление о дедлайне отправлено"""
    db = SessionLocal()
    try:
        deadline = db.query(Deadline).filter(
            Deadline.moodle_user_id == moodle_user_id,
            Deadline.assignment_name == assignment_name
        ).first()
        if deadline:
            deadline.notified_week_before = True
            db.commit()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        db.close()