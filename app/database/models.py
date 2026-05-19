from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text, JSON
)
from datetime import datetime
from app.database.db import Base

class UserLink(Base):
    __tablename__ = "user_links"
    
    id = Column(Integer, primary_key=True)
    vk_user_id = Column(Integer, unique=True, nullable=False)
    moodle_user_id = Column(Integer, nullable=False)
    moodle_username = Column(String(100), nullable=False)
    moodle_fullname = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_notification_grade = Column(Float, default=0)
    last_notification_risk = Column(String(50))
    notification_type = Column(String(50), default="all")
    selected_course_id = Column(Integer, default=0)      # ← добавить
    selected_course_name = Column(String(200), default="")  # ← добавить

class Course(Base):
    """Дисциплины студента"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True)
    moodle_user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    course_name = Column(String(200), nullable=False)
    course_shortname = Column(String(100))
    last_sync = Column(DateTime, default=datetime.utcnow)


class Grade(Base):
    """Оценки по дисциплинам"""
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True)
    moodle_user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    course_name = Column(String(200))
    item_name = Column(String(200))
    grade_value = Column(Float)
    grade_raw = Column(String(50))
    graded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_new = Column(Boolean, default=False)


class Deadline(Base):
    """Дедлайны заданий"""
    __tablename__ = "deadlines"
    
    id = Column(Integer, primary_key=True)
    moodle_user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    course_name = Column(String(200))
    assignment_name = Column(String(200))
    deadline = Column(DateTime)
    description = Column(Text)
    is_overdue = Column(Boolean, default=False)
    notified_week_before = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True)
    vk_user_id = Column(Integer, nullable=False)
    moodle_user_id = Column(Integer)
    message_text = Column(String(1000))
    notification_type = Column(String(50))  # grade, deadline, risk
    risk_level = Column(String(50))  # HIGH_RISK, MEDIUM_RISK, LOW_RISK, MANUAL
    avg_grade = Column(Float)  # средний балл
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Integer, default=1)
    error_message = Column(String(500))