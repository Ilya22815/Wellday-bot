import requests
import time

HEADERS = {
    "User-Agent": "WelldayLeadFinder/1.0",
    "Accept": "application/json",
    "HH-User-Agent": "WelldayLeadFinder/1.0 (wellday@well-day.ru)"
}

HH_EMPLOYER_SIZES = {
    "from 1 to 10": 5,
    "from 10 to 50": 30,
    "from 50 to 100": 75,
    "from 100 to 500": 300,
    "from 500 to 1000": 750,
    "more than 1000": 2000,
}

MOSCOW_AREA = "1"


def get_companies(pages=5, per_page=50, min_vacancies=3):
    """
    Получает компании из Москвы через hh.ru API.
    Запускать локально — hh.ru блокирует облачные серверы.
    min_vacancies — минимум открытых вакансий (косвенный признак размера).
    """
    companies = []
    seen_ids = set()

    for page in range(pages):
        try:
            resp = requests.get(
                "https://api.hh.ru/employers",
                params={
                    "area": MOSCOW_AREA,
                    "type": "company",
                    "per_page": per_page,
                    "page": page,
                    "only_with_vacancies": True,
                },
                headers=HEADERS,
                timeout=10
            )
            if resp.status_code != 200:
                print(f"[hh.ru] Страница {page}: статус {resp.status_code}")
                break

            items = resp.json().get("items", [])
            if not items:
                break

            for item in items:
                emp_id = item.get("id")
                if emp_id in seen_ids:
                    continue
                seen_ids.add(emp_id)

                open_vac = item.get("open_vacancies", 0)
                if open_vac < min_vacancies:
                    continue

                detail = _get_employer_detail(emp_id)
                if detail:
                    companies.append(detail)

                time.sleep(0.25)

        except Exception as e:
            print(f"[hh.ru] Ошибка на странице {page}: {e}")
            break

    return companies


def _get_employer_detail(employer_id):
    try:
        resp = requests.get(
            f"https://api.hh.ru/employers/{employer_id}",
            headers=HEADERS,
            timeout=10
        )
        if resp.status_code != 200:
            return None

        d = resp.json()

        size_label = d.get("size", {})
        if isinstance(size_label, dict):
            size_label = size_label.get("name", "")

        employee_count = HH_EMPLOYER_SIZES.get(size_label, 0)

        return {
            "id": employer_id,
            "name": d.get("name", ""),
            "site_url": d.get("site_url", ""),
            "hh_url": d.get("alternate_url", ""),
            "description": (d.get("description") or "")[:300],
            "industries": [i.get("name", "") for i in d.get("industries", [])],
            "open_vacancies": d.get("open_vacancies", 0),
            "employee_count": employee_count,
            "area": (d.get("area") or {}).get("name", ""),
            "trusted": d.get("trusted", False),
        }
    except Exception as e:
        print(f"[hh.ru] Детали {employer_id}: {e}")
        return None
