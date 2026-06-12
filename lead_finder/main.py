from email_finder import find_emails_on_site
from scorer import score
from letter_generator import generate_letter

TELEGRAM_TOKEN   = "8834041003:AAEM1rx_yp19xqrZt6j3E1GAjGbfwwRWi2o"
TELEGRAM_CHAT_ID = "8819726375"
GIS_API_KEY      = "ece1b98f-ad93-4671-b213-22d108a36b71"
HH_CLIENT_ID     = ""
MIN_SCORE        = 30


def collect_companies():
    companies = []
    seen = set()

    if GIS_API_KEY:
        from gis_parser import get_companies as gis_get
        print("Ищем через 2GIS...")
        gis_companies = gis_get(api_key=GIS_API_KEY)
        for c in gis_companies:
            key = c["name"].lower().strip()
            if key not in seen:
                seen.add(key)
                c["source"] = "2GIS"
                companies.append(c)
        print(f"   2GIS: {len(gis_companies)} компаний")

    if HH_CLIENT_ID:
        from hh_parser import get_companies as hh_get
        print("Ищем через hh.ru...")
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

    return companies


def save_excel(hot_leads):
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Лиды"

    headers    = ["Компания", "Score", "Отрасль", "Телефон", "Email", "Сайт", "Адрес", "Письмо"]
    col_widths = [35, 8, 25, 20, 30, 30, 35, 80]

    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2E75B6")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[chr(64 + col)].width = width

    ws.row_dimensions[1].height = 20

    for row_num, c in enumerate(hot_leads, 2):
        values = [
            c.get("name"),
            c.get("score"),
            ", ".join(c.get("industries", [])),
            c.get("phone") or "—",
            ", ".join(c.get("emails", [])[:2]),
            c.get("site_url") or "—",
            c.get("address") or "—",
            c.get("letter", ""),
        ]
        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row_num].height = 80

    wb.save("leads.xlsx")
    print("Готово! Открой файл leads.xlsx")


def run():
    if not GIS_API_KEY and not HH_CLIENT_ID:
        print("Нет ни одного ключа!")
        return

    companies = collect_companies()
    print(f"\nВсего компаний: {len(companies)}")

    if not companies:
        print("Компании не найдены.")
        return

    hot_leads = []

    for i, company in enumerate(companies, 1):
        name = company.get("name", "")
        site = company.get("site_url", "")

        print(f"[{i}/{len(companies)}] {name}")

        emails = find_emails_on_site(site) if site else []
        company["emails"] = emails

        s = score(company)
        company["score"] = s

        phone = company.get("phone") or "нет"
        found = emails[:1] if emails else ("сайт: " + site if site else "не найдено")
        print(f"   score={s} | тел={phone} | email={found}")

        if s >= MIN_SCORE:
            letter = generate_letter(company)
            company["letter"] = letter
            hot_leads.append(company)

    print(f"\nГорячих лидов: {len(hot_leads)}")
    save_excel(hot_leads)


if __name__ == "__main__":
    run()
