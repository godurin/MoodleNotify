from app.services.risk import detect_risk, get_recommendation

print("📊 Проверка расчёта рисков")

# Тестовые значения
test_grades = [1.5, 2.5, 3.5, 4.5, 5.5, 7.0, 8.5, 10.0]

print("\nОценка -> Уровень риска:")
print("-" * 40)
for grade in test_grades:
    risk, message = detect_risk(grade)
    recs = get_recommendation(risk, grade)
    print(f"{grade:5.1f} -> {risk:12} | {message[:40]}...")

print("\n✨ Проверка завершена")