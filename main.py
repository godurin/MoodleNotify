from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path
import threading
import time
import os
from fastapi.responses import HTMLResponse

from app.scheduler.jobs import start_scheduler
from app.config import settings

bot_thread = None

# Настройка шаблонов
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "web" / "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 ЗАПУСК MOODLENOTIFY")
    print("="*50)
    
    print("📅 Запуск планировщика...")
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Планировщик запущен")
    
    print("🤖 Запуск VK бота...")
    try:
        from app.vk.bot import run_bot
        
        def run_bot_with_reconnect():
            while True:
                try:
                    run_bot()
                except Exception as e:
                    print(f"❌ Ошибка в боте: {e}")
                    time.sleep(10)
        
        bot_thread = threading.Thread(target=run_bot_with_reconnect, daemon=True)
        bot_thread.start()
        print("✅ VK бот запущен")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
    
    print("\n✨ Система готова к работе")
    print(f"⏱️  Интервал проверки: {settings.CHECK_INTERVAL_MINUTES} минут")
    print(f"🔧 Админ панель: http://localhost:8000/admin/login")
    print("="*50 + "\n")
    
    yield
    
    print("\n🛑 Остановка MoodleNotify...")

app = FastAPI(
    title="MoodleNotify API",
    description="Система информирования студентов об успеваемости",
    version="1.0.0",
    lifespan=lifespan
)

# ========== СТАРЫЕ МАРШРУТЫ (оставляем как есть) ==========
@app.get("/")
def root():
    return {
        "status": "MoodleNotify работает",
        "check_interval_minutes": settings.CHECK_INTERVAL_MINUTES
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "bot_running": bot_thread is not None and bot_thread.is_alive() if bot_thread else False
    }

@app.get("/stats")
def get_statistics():
    from app.database.service import get_stats
    return get_stats()


# ========== НОВЫЕ МАРШРУТЫ ДЛЯ АДМИНКИ ==========

# Простая аутентификация
def check_auth(request: Request):
    admin_auth = request.cookies.get("admin_auth")
    if not admin_auth and request.url.path not in ["/admin/login", "/admin/login-post"]:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return True

@app.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/admin/login-post")
def admin_login(request: Request, password: str = Form(...)):
    if password == settings.ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(key="admin_auth", value="true")
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})

@app.get("/admin/dashboard", dependencies=[Depends(check_auth)])
def admin_dashboard(request: Request):
    from app.database.service import get_stats
    stats = get_stats()
    
    # Формируем HTML вручную
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MoodleNotify Admin</title>
        <style>
            body {{ font-family: Arial; margin:0; padding:0; background:#f0f2f5; }}
            .header {{ background:#1e3c72; color:white; padding:15px 20px; }}
            .nav {{ background:#2a5298; padding:10px 20px; }}
            .nav a {{ color:white; text-decoration:none; margin-right:20px; }}
            .container {{ padding:20px; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
            .stat-card {{ background:white; padding:20px; border-radius:10px; min-width:150px; }}
            .stat-card h3 {{ margin:0 0 10px 0; }}
            .stat-card p {{ font-size:36px; margin:0; }}
            table {{ width:100%; border-collapse:collapse; background:white; }}
            th, td {{ border:1px solid #ddd; padding:8px; text-align:left; }}
            th {{ background:#1e3c72; color:white; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 MoodleNotify Admin Panel</h1>
        </div>
        <div class="nav">
            <a href="/admin/dashboard">Дашборд</a>
            <a href="/admin/logs">Логи</a>
            <a href="/admin/settings">Настройки</a>
            <a href="/admin/manual">Ручная отправка</a>
        </div>
        <div class="container">
            <h2>📈 Статистика системы</h2>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>👥 Пользователей</h3>
                    <p>{stats['total_users']}</p>
                </div>
                <div class="stat-card">
                    <h3>📨 Уведомлений</h3>
                    <p>{stats['total_notifications']}</p>
                </div>
                <div class="stat-card">
                    <h3>⚠️ Группа риска</h3>
                    <p>{stats['high_risk_users']}</p>
                </div>
            </div>

            <h3>📋 Последние уведомления</h3>
            <table>
                <thead>
                    <tr><th>VK ID</th><th>Риск</th><th>Средний балл</th><th>Время</th><th>Статус</th></tr>
                </thead>
                <tbody>
    """
    
    for log in stats['recent_logs']:
        html += f"""
                    <tr>
                        <td>{log['vk_user_id']}</td>
                        <td>{log['risk_level'] or '-'}</td>
                        <td>{log['avg_grade'] or '-'}</td>
                        <td>{log['sent_at'] or '-'}</td>
                        <td>✅</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(html)


@app.get("/admin/logs", dependencies=[Depends(check_auth)])
def admin_logs(request: Request):
    from app.database.db import SessionLocal
    from app.database.models import NotificationLog, UserLink
    
    db = SessionLocal()
    logs = db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(100).all()
    
    # Обогащаем логи именами пользователей
    enriched_logs = []
    for log in logs:
        user = db.query(UserLink).filter(UserLink.vk_user_id == log.vk_user_id).first()
        enriched_logs.append({
            "id": log.id,
            "username": user.moodle_username if user else str(log.vk_user_id),
            "vk_user_id": log.vk_user_id,
            "risk_level": log.risk_level,
            "avg_grade": log.avg_grade,
            "sent_at": log.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log.sent_at else "-",
            "success": log.success
        })
    db.close()
    
    # Формируем HTML вручную
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MoodleNotify - Логи</title>
        <style>
            body { font-family: Arial; margin:0; padding:0; background:#f0f2f5; }
            .header { background:#1e3c72; color:white; padding:15px 20px; }
            .nav { background:#2a5298; padding:10px 20px; }
            .nav a { color:white; text-decoration:none; margin-right:20px; }
            .container { padding:20px; }
            table { width:100%; border-collapse:collapse; background:white; }
            th, td { border:1px solid #ddd; padding:8px; text-align:left; }
            th { background:#1e3c72; color:white; }
            .success { color:green; }
            .error { color:red; }
        </style>
    </head>
    <body>
        <div class="header"><h1>📊 MoodleNotify Admin Panel</h1></div>
        <div class="nav">
            <a href="/admin/dashboard">Дашборд</a>
            <a href="/admin/logs">Логи</a>
            <a href="/admin/settings">Настройки</a>
            <a href="/admin/manual">Ручная отправка</a>
        </div>
        <div class="container">
            <h2>📝 Все уведомления</h2>
            <table>
                <thead><tr><th>ID</th><th>Пользователь</th><th>VK ID</th><th>Риск</th><th>Средний балл</th><th>Время</th><th>Статус</th></tr></thead>
                <tbody>
    """
    
    for log in enriched_logs:
        status_class = "success" if log['success'] else "error"
        status_text = "✅" if log['success'] else "❌"
        html += f"""
                    <tr>
                        <td>{log['id']}</td>
                        <td>{log['username']}</td>
                        <td>{log['vk_user_id']}</td>
                        <td>{log['risk_level'] or '-'}</td>
                        <td>{log['avg_grade'] or '-'}</td>
                        <td>{log['sent_at']}</td>
                        <td class="{status_class}">{status_text}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(html)

@app.get("/admin/settings", dependencies=[Depends(check_auth)])
def admin_settings_page(request: Request, saved: bool = False):
    from app.config import settings
    
    saved_msg = '<div style="background:#d4edda;color:#155724;padding:10px;border-radius:5px;margin-bottom:20px;">✅ Настройки сохранены!</div>' if saved else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MoodleNotify - Настройки</title>
        <style>
            body {{ font-family: Arial; margin:0; padding:0; background:#f0f2f5; }}
            .header {{ background:#1e3c72; color:white; padding:15px 20px; }}
            .nav {{ background:#2a5298; padding:10px 20px; }}
            .nav a {{ color:white; text-decoration:none; margin-right:20px; }}
            .container {{ padding:20px; }}
            .form-group {{ margin-bottom:15px; }}
            label {{ display:block; margin-bottom:5px; font-weight:bold; }}
            input[type=number] {{ padding:8px; width:200px; }}
            button {{ background:#2a5298; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; }}
            .card {{ background:white; padding:20px; border-radius:10px; max-width:500px; }}
            .hint {{ color:#666; font-size:12px; margin-top:5px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>📊 MoodleNotify Admin Panel</h1></div>
        <div class="nav">
            <a href="/admin/dashboard">Дашборд</a>
            <a href="/admin/logs">Логи</a>
            <a href="/admin/settings">Настройки</a>
            <a href="/admin/manual">Ручная отправка</a>
        </div>
        <div class="container">
            <div class="card">
                <h2>⚙️ Настройки системы</h2>
                {saved_msg}
                <form method="post" action="/admin/settings">
                    <div class="form-group">
                        <label>Порог высокого риска (0-100):</label>
                        <input type="number" step="1" min="0" max="100" name="high_threshold" value="{settings.HIGH_RISK_THRESHOLD}">
                        <div class="hint">⚠️ Ниже этого балла — студент в группе ВЫСОКОГО риска (нужна срочная помощь)</div>
                    </div>
                    <div class="form-group">
                        <label>Порог среднего риска (0-100):</label>
                        <input type="number" step="1" min="0" max="100" name="medium_threshold" value="{settings.MEDIUM_RISK_THRESHOLD}">
                        <div class="hint">🟡 Ниже этого балла — студент в группе СРЕДНЕГО риска (стоит подтянуть оценки)</div>
                    </div>
                    <div class="form-group">
                        <label>Интервал проверки (минуты):</label>
                        <input type="number" step="1" min="1" name="check_interval" value="{settings.CHECK_INTERVAL_MINUTES}">
                        <div class="hint">⏱️ Как часто проверять оценки в Moodle</div>
                    </div>
                    <button type="submit">💾 Сохранить</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/admin/settings", dependencies=[Depends(check_auth)])
def admin_settings_save(
    high_threshold: float = Form(...),
    medium_threshold: float = Form(...),
    check_interval: int = Form(...)
):
    import importlib
    import sys
    
    # Обновляем .env файл
    env_path = BASE_DIR / ".env"
    
    # Читаем существующие переменные
    env_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
    
    # Обновляем значения
    env_vars["HIGH_RISK_THRESHOLD"] = str(high_threshold)
    env_vars["MEDIUM_RISK_THRESHOLD"] = str(medium_threshold)
    env_vars["CHECK_INTERVAL_MINUTES"] = str(check_interval)
    
    # Записываем обратно
    with open(env_path, "w", encoding="utf-8") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    # Перезагружаем модуль config
    import app.config
    importlib.reload(app.config)
    
    # Обновляем глобальный settings
    from app.config import settings as new_settings
    global settings
    settings = new_settings
    
    # Обновляем интервал планировщика
    try:
        from apscheduler.triggers.interval import IntervalTrigger
        from app.scheduler.jobs import scheduler
        job = scheduler.get_job('check_students')
        if job:
            job.reschedule(trigger=IntervalTrigger(minutes=check_interval))
            print(f"✅ Интервал планировщика обновлён на {check_interval} минут")
    except Exception as e:
        print(f"Ошибка обновления планировщика: {e}")

@app.get("/admin/manual", dependencies=[Depends(check_auth)])
def manual_notify_page(request: Request, sent: bool = False):
    from app.database.service import get_all_links
    users = get_all_links()
    
    sent_msg = '<div style="background:#d4edda;color:#155724;padding:10px;border-radius:5px;margin-bottom:20px;">✅ Уведомление отправлено!</div>' if sent else ''
    
    options = ""
    for user in users:
        options += f'<option value="{user.vk_user_id}">{user.moodle_username} ({user.moodle_fullname}) - VK: {user.vk_user_id}</option>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MoodleNotify - Ручная отправка</title>
        <style>
            body {{ font-family: Arial; margin:0; padding:0; background:#f0f2f5; }}
            .header {{ background:#1e3c72; color:white; padding:15px 20px; }}
            .nav {{ background:#2a5298; padding:10px 20px; }}
            .nav a {{ color:white; text-decoration:none; margin-right:20px; }}
            .container {{ padding:20px; }}
            .form-group {{ margin-bottom:15px; }}
            label {{ display:block; margin-bottom:5px; font-weight:bold; }}
            select, textarea {{ padding:8px; width:100%; max-width:400px; }}
            textarea {{ height:150px; }}
            button {{ background:#2a5298; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; }}
            .card {{ background:white; padding:20px; border-radius:10px; max-width:600px; }}
        </style>
    </head>
    <body>
        <div class="header"><h1>📊 MoodleNotify Admin Panel</h1></div>
        <div class="nav">
            <a href="/admin/dashboard">Дашборд</a>
            <a href="/admin/logs">Логи</a>
            <a href="/admin/settings">Настройки</a>
            <a href="/admin/manual">Ручная отправка</a>
        </div>
        <div class="container">
            <div class="card">
                <h2>📨 Ручная отправка уведомления</h2>
                {sent_msg}
                <form method="post" action="/admin/manual">
                    <div class="form-group">
                        <label>Выберите пользователя:</label>
                        <select name="vk_user_id">
                            {options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Текст сообщения:</label>
                        <textarea name="message" placeholder="Введите текст уведомления..."></textarea>
                    </div>
                    <button type="submit">📤 Отправить</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/admin/manual", dependencies=[Depends(check_auth)])
def manual_notify_send(
    vk_user_id: int = Form(...),
    message: str = Form(...)
):
    from app.services.notify import send_message
    from app.database.service import save_notification_log
    
    success = send_message(vk_user_id, message)
    
    save_notification_log(
        vk_user_id=vk_user_id,
        moodle_user_id=None,
        message=message,
        risk_level="MANUAL",
        avg_grade=0,
        success=success
    )
    
    return RedirectResponse(url="/admin/manual?sent=true", status_code=303)

# Страница логина (отдельная, без шаблона)
@app.get("/admin/login-page")
def login_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Вход в админку</title>
        <style>
            body { font-family: Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 300px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { width: 100%; padding: 10px; background: #1e3c72; color: white; border: none; border-radius: 5px; cursor: pointer; }
            h2 { text-align: center; margin-bottom: 20px; }
            .error { color: red; text-align: center; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>🔐 Вход в MoodleNotify</h2>
            <form method="post" action="/admin/login-post">
                <input type="password" name="password" placeholder="Пароль администратора" required>
                <button type="submit">Войти</button>
            </form>
        </div>
    </body>
    </html>
    """)

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)