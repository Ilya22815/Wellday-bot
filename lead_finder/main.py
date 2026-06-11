"""
Wellday Lead Finder V5
======================
Ищет компании в Москве через 2GIS,
находит email на сайте компании,
генерирует письмо под отрасль,
отправляет карточки лида в Telegram.

Запуск: python main.py
"""

import pandas as pd
from gis_parser import get_companies
from email_finder import find_emails_on_site, generate_email_patterns
from scorer import score
from letter_generator import generate_letter
from telegram_sender import send_lead, send_summary

# ============================================================
# КОНФИГ
# ============================================================
TELEGRAM_TOKEN = "8834041003:AAEM1rx_yp19xqrZt6j3E1GAjGbfwwRWi2o"
TELEGRAM_CHAT_ID = "8819726375"
GIS_API_KEY = ""        # вставь ключ с dev.2gis.ru
MIN_SCORE = 50          # минимальный score для отправки
# ============================================================


def run():
    if not GIS_API_KEY:
        print("❌ Вставь GIS_API_KEY в main.py!")
        return

    print("🔍 Ищем компании через 2GIS...")
    companies = get_companies(api_key=GIS_API_KEY)
    print(f"✅ Найдено компаний: {len(companies)}")

    hot_leads = []

    for i, company in enumerate(companies, 1):
        name = company.get("name", "")
        site = company.get("site_url", "")

        print(f"[{i}/{len(companies)}] {name}")

        # Ищем email на сайте компании
        emails = find_emails_on_site(site) if site else []
        if not emails:
            emails = generate_email_patterns(name, site)
        company["emails"] = emails

        # Скоринг
        s = score(company)
        company["score"] = s

        phone = company.get("phone") or "—"
        print(f"   score={s} | тел={phone} | email={emails[:1]}")

        if s >= MIN_SCORE:
            letter = generate_letter(company)
            company["letter"] = letter
            hot_leads.append(company)

            # Отправляем в Telegram
            send_lead(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, company, letter)

    print(f"\n📊 Горячих лидов (score ≥ {MIN_SCORE}): {len(hot_leads)}")

    # Сохраняем в CSV
    rows = []
    for c in hot_leads:
        rows.append({
            "Компания": c.get("name"),
            "Score": c.get("score"),
            "Отрасль": ", ".join(c.get("industries", [])),
            "Телефон": c.get("phone"),
            "Email": ", ".join(c.get("emails", [])[:2]),
            "Сайт": c.get("site_url"),
            "Адрес": c.get("address"),
            "Письмо": c.get("letter", "").replace("\n", " "),
        })

    df = pd.DataFrame(rows)
    df.to_csv("leads.csv", index=False, encoding="utf-8-sig", sep=";")
    print("💾 Сохранено в leads.csv")

    send_summary(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, len(companies), len(hot_leads))


if __name__ == "__main__":
    run()
