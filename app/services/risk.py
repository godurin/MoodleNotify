from app.config import settings

def detect_risk(avg_grade):
    """
    Определение уровня риска на основе среднего балла (0-100)
    Возвращает: (risk_level, message)
    """
    if avg_grade < settings.HIGH_RISK_THRESHOLD:
        return "HIGH_RISK", "🔴 ВЫСОКИЙ РИСК: У вас есть задолженности! Нужно срочно исправлять ситуацию."
    elif avg_grade < settings.MEDIUM_RISK_THRESHOLD:
        return "MEDIUM_RISK", "🟡 СРЕДНИЙ РИСК: Ваша успеваемость ниже среднего, стоит подтянуть оценки."
    else:
        return "LOW_RISK", "🟢 НИЗКИЙ РИСК: Вы хорошо учитесь, продолжайте в том же духе!"