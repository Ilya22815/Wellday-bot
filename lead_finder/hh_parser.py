import requests
import time

HH_API = "https://api.hh.ru"
MOSCOW_AREA = "1"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "WelldayBot/1.0 (wellday@well-day.ru)",
    "Accept": "application/json",
    "HH-User-Agent": "WelldayBot/1.0 (wellday@well-day.ru)",
})

# ID отраслей в hh.ru (для фильтрации вакансий)
INDUSTRIES = [
    ("7",  "Информационные технологии"),
    ("9",  "Финансы"),
    ("10", "Консалтинг"),
    ("13", "Маркетинг и реклама"),
    ("23", "Фармацевтика"),
    ("5",  "Телекоммуникации"),
    ("6",  "Страхование"),
    ("3",  "Банки"),
]


def get_companies(pages_per_industry=5, min_vacancies=0):
    """
    Получаем компании через публичный endpoint /vacancies (не требует OAuth).
    Из вакансий извлекаем уникальных работодателей, затем
    пробуем получить детали через /employers/{id}.
    """
    companies = []
    seen_ids = set()

    for industry_id, industry_name in INDUSTRIES:
        print(f"[hh.ru] Отрасль: {industry_name}...")
        found_in_industry = 0

        for page in range(pages_per_industry):
            try:
                resp = SESSION.get(
                    f"{HH_API}/vacancies",
                    params={
                        "area": MOSCOW_AREA,
                        "industry": industry_id,
                        "per_page": 100,
                        "page": page,
                        "only_with_salary": False,
                    },
                    timeout=10,
                )

                if resp.status_code != 200:
                    print(f"[hh.ru] Статус {resp.status_code}: {resp.text[:200]}")
                    break

                data = resp.json()
                items = data.get("items", [])

                if not items:
                    break

                for vacancy in items:
                    employer = vacancy.get("employer") or {}
                    emp_id = employer.get("id")
                    if not emp_id or emp_id in seen_ids:
                        continue
                    seen_ids.add(emp_id)

                    # Пробуем получить детали (site_url, open_vacancies)
                    detail = _get_detail(emp_id)

                    if detail is None:
                        # Используем минимальные данные из вакансии
                        name = employer.get("name", "").strip()
                        if not name:
                            continue
                        detail = {
                            "name": name,
                            "phone": None,
                            "site_url": "",
                            "address": "",
                            "open_vacancies": 0,
                            "employee_count": 0,
                            "trusted": employer.get("trusted", False),
                            "emails": [],
                        }

                    if detail.get("open_vacancies", 0) < min_vacancies:
                        continue

                    detail["industries"] = [industry_name]
                    companies.append(detail)
                    found_in_industry += 1

                    time.sleep(0.2)

                pages_total = data.get("pages", 1)
                if page + 1 >= pages_total:
                    break

                time.sleep(0.5)

            except Exception as e:
                print(f"[hh.ru] Ошибка: {e}")
                break

        print(f"[hh.ru]   Найдено: {found_in_industry}")
        time.sleep(0.5)

    print(f"[hh.ru] Итого: {len(companies)} компаний")
    return companies


def _get_detail(employer_id):
    try:
        resp = SESSION.get(
            f"{HH_API}/employers/{employer_id}",
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        d = resp.json()
        name = d.get("name", "").strip()
        if not name:
            return None

        size_label = (d.get("size") or {}).get("name", "")

        return {
            "name": name,
            "phone": None,
            "site_url": d.get("site_url") or "",
            "address": "",
            "open_vacancies": d.get("open_vacancies", 0),
            "employee_count": _parse_size(size_label),
            "trusted": d.get("trusted", False),
            "emails": [],
        }
    except Exception:
        return None


def _parse_size(label):
    for key, val in [
        ("более 1000", 2000), ("more than 1000", 2000),
        ("от 500", 750),      ("from 500", 750),
        ("от 100", 300),      ("from 100", 300),
        ("от 50", 75),        ("from 50", 75),
        ("от 10", 30),        ("from 10", 30),
    ]:
        if key in label:
            return val
    return 0
