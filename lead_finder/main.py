"""
Wellday Lead Finder V5
======================
Источники данных (работают вместе):
  - 2GIS API     → компании с телефонами (нужен ключ dev.2gis.ru)
  - hh.ru API    → компании с вакансиями (нужен ключ dev.hh.ru)

Запуск: python main.py
"""

import pandas as pd
from email_finder import find_emails_on_site, generate_email_patterns
from scorer import score
from letter_generator import generate_letter
from telegram_sender import send_lead, send_summary

# ============================================================
# КОНФИГ — вставляй ключи по мере получения
# ============================================================
TELEGRAM_TOKEN  = "8834041003:AAEM1rx_yp19xqrZt6j3E1GAjGbfwwRWi2o"
TELEGRAM_CHAT_ID = "8819726375"

GIS_API_KEY  = "ece1b98f-ad93-4671-b213-22d108a36b71"   # 2GIS API key
HH_CLIENT_ID = ""   # ключ с dev.hh.ru    (придёт после проверки)

MIN_SCORE = 50
# ============================================================


def collect_companies():
    companies = []
    seen = set()

    # --- 2GIS ---
    if GIS_API_KEY:
        from gis_parser import get_companies as gis_get
        print("🔍 Ищем через 2GIS...")
        gis_companies = gis_get(api_key=GIS_API_KEY)
        for c in gis_companies:
            key = c["name"].lower().strip()
            if key not in seen:
                seen.add(key)
                c["source"] = "2GIS"
                companies.append(c)
        print(f"   2GIS: {len(gis_companies)} компаний")
    else:
        print("⚠️  2GIS ключ не указан — пропускаем")

    # --- hh.ru ---
    if HH_CLIENT_ID:
        from hh_parser import get_companies as hh_get
        print("🔍 Ищем через hh.ru...")
        hh_companies = hh_get(client_id=HH_CLIENT_ID)
        added = 0
        for c in hh_companies:
            key = c["name"].lower().strip()
            if key not in seen:
                seen.add(key)
                c["source"] = "hh.ru"
                companies.append(c)
                added += 1
        print(f"   hh.ru: {added} новых компаний")
    else:
        print("⚠️  hh.ru ключ не указан — пропускаем (ждём одобрения)")

    return companies


def run():
    if not GIS_API_KEY and not HH_CLIENT_ID:
        print("❌ Нет ни одного ключа! Заполни GIS_API_KEY или HH_CLIENT_ID в main.py")
        return

    companies = collect_companies()
    print(f"\n✅ Всего компаний: {len(companies)}")

    if not companies:
        print("Компании не найдены. Проверь ключи.")
        return

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

        # Скоринг
        s = score(company)
        company["score"] = s

        phone = company.get("phone") or "—"
        print(f"   score={s} | тел={phone} | email={emails[:1]}")

        if s >= MIN_SCORE:
            letter = generate_letter(company)
            company["letter"] = letter
            hot_leads.append(company)
            send_lead(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, company, letter)

    print(f"\n📊 Горячих лидов (score ≥ {MIN_SCORE}): {len(hot_leads)}")

    # Сохраняем в CSV
    rows = []
    for c in hot_leads:
        rows.append({
            "Компания":  c.get("name"),
            "Score":     c.get("score"),
            "Источник":  c.get("source"),
            "Отрасль":   ", ".join(c.get("industries", [])),
            "Телефон":   c.get("phone"),
            "Email":     ", ".join(c.get("emails", [])[:2]),
            "Сайт":      c.get("site_url"),
            "Адрес":     c.get("address", ""),
            "Письмо":    c.get("letter", "").replace("\n", " "),
        })

    df = pd.DataFrame(rows)
    df.to_csv("leads.csv", index=False, encoding="utf-8-sig", sep=";")
    print("💾 Сохранено в leads.csv")

    send_summary(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, len(companies), len(hot_leads))


if __name__ == "__main__":
    run()
