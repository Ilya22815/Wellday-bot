import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_lead(token, chat_id, company, letter):
    """Отправляет карточку лида в Telegram."""
    name = company.get("name", "—")
    phone = company.get("phone") or "не найден"
    emails = company.get("emails") or []
    email_str = ", ".join(emails[:2]) if emails else "не найден"
    site = company.get("site_url") or "—"
    industries = ", ".join(company.get("industries", [])) or "—"
    score = company.get("score", 0)
    emp = company.get("employee_count", 0)
    vac = company.get("open_vacancies", 0)

    emp_str = f"{emp}+" if emp else f"~{vac} вакансий"

    text = (
        f"🏢 *{name}*\n"
        f"🔥 Score: {score}/100\n"
        f"👥 Сотрудников: {emp_str}\n"
        f"📋 Отрасль: {industries}\n"
        f"📞 Телефон: {phone}\n"
        f"📧 Email: {email_str}\n"
        f"🌐 Сайт: {site}\n\n"
        f"✉️ *Письмо:*\n"
        f"```\n{letter[:800]}\n```"
    )

    try:
        resp = requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[Telegram] Ошибка: {e}")
        return False


def send_summary(token, chat_id, total, hot):
    text = (
        f"✅ *Поиск завершён*\n"
        f"Найдено компаний: {total}\n"
        f"Горячих лидов (score ≥ 60): {hot}"
    )
    try:
        requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception:
        pass
