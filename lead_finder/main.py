"""
Wellday Lead Finder V5
======================
Ищет компании в Москве с 50+ сотрудниками через hh.ru и 2GIS,
находит email и телефон, генерирует письмо, отправляет в Telegram.

Запуск: python main.py

Нужно заполнить конфиг ниже.
"""

import pandas as pd
from hh_parser import get_companies
from gis_parser import get_phone_by_name
from email_finder import find_emails_on_site, generate_email_patterns
from scorer import score
from letter_generator import generate_letter
from telegram_sender import send_lead, send_summary

# ============================================================
# КОНФИГ — заполни перед запуском
# ============================================================
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_БОТА"      # создать через @BotFather
TELEGRAM_CHAT_ID = "ВАШ_CHAT_ID"       # узнать через @userinfobot
GIS_API_KEY = ""                         # dev.2gis.ru (бесплатно, опционально)
MIN_SCORE = 60                           # минимальный score для отправки в Telegram
HH_PAGES = 5                             # кол-во страниц hh.ru (50 компаний каждая)
# ============================================================


def run():
    print("🔍 Ищем компании на hh.ru...")
    companies = get_companies(pages=HH_PAGES, per_page=50, min_vacancies=3)
    print(f"✅ Найдено компаний: {len(companies)}")

    hot_leads = []

    for i, company in enumerate(companies, 1):
        name = company.get("name", "")
        site = company.get("site_url", "")

        print(f"[{i}/{len(companies)}] {name}")

        # Ищем email на сайте
        emails = find_emails_on_site(site) if site else []
        if not emails:
            emails = generate_email_patterns(name, site)
        company["emails"] = emails

        # Ищем телефон через 2GIS (если есть ключ)
        phone = get_phone_by_name(name, GIS_API_KEY) if GIS_API_KEY else None
        company["phone"] = phone

        # Скоринг
        s = score(company)
        company["score"] = s

        print(f"   score={s} | email={emails[:1]} | phone={phone}")

        if s >= MIN_SCORE:
            letter = generate_letter(company)
            company["letter"] = letter
            hot_leads.append(company)

            # Отправляем в Telegram
            if TELEGRAM_TOKEN != "ВАШ_ТОКЕН_БОТА":
                send_lead(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, company, letter)

    print(f"\n📊 Горячих лидов (score ≥ {MIN_SCORE}): {len(hot_leads)}")

    # Сохраняем в CSV
    rows = []
    for c in hot_leads:
        rows.append({
            "Компания": c.get("name"),
            "Score": c.get("score"),
            "Сотрудников": c.get("employee_count"),
            "Вакансий": c.get("open_vacancies"),
            "Отрасль": ", ".join(c.get("industries", [])),
            "Телефон": c.get("phone"),
            "Email": ", ".join(c.get("emails", [])[:2]),
            "Сайт": c.get("site_url"),
            "hh.ru": c.get("hh_url"),
            "Письмо": c.get("letter", "").replace("\n", " "),
        })

    df = pd.DataFrame(rows)
    df.to_csv("leads.csv", index=False, encoding="utf-8-sig", sep=";")
    print("💾 Сохранено в leads.csv")

    # Итог в Telegram
    if TELEGRAM_TOKEN != "ВАШ_ТОКЕН_БОТА":
        send_summary(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, len(companies), len(hot_leads))


if __name__ == "__main__":
    run()
