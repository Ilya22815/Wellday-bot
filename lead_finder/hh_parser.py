import requests
from bs4 import BeautifulSoup
import time
import re

# Отрасли hh.ru которые нас интересуют (IT, финансы, консалтинг, маркетинг, фарма)
INDUSTRIES = [
    "7",    # Информационные технологии
    "9",    # Финансы
    "10",   # Консалтинг
    "13",   # Маркетинг, реклама, PR
    "23",   # Фармацевтика
    "5",    # Телекоммуникации
]

MOSCOW_AREA = "1"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://hh.ru/",
})


def get_companies(pages_per_industry=2, min_vacancies=2):
    """
    Скрапит hh.ru/employers_company — работает как обычный браузер.
    Возвращает список компаний Москвы по нужным отраслям.
    """
    # Сначала заходим на главную — получаем куки
    try:
        SESSION.get("https://hh.ru/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    companies = []
    seen_ids = set()

    for industry in INDUSTRIES:
        for page in range(pages_per_industry):
            try:
                url = "https://hh.ru/employers_company"
                params = {
                    "area": MOSCOW_AREA,
                    "industry": industry,
                    "page": page,
                }
                resp = SESSION.get(url, params=params, timeout=10)

                if resp.status_code != 200:
                    print(f"[hh.ru] отрасль={industry} стр={page}: статус {resp.status_code}")
                    break

                items = _parse_employers_page(resp.text)

                for item in items:
                    emp_id = item.get("id")
                    if not emp_id or emp_id in seen_ids:
                        continue
                    seen_ids.add(emp_id)

                    # Получаем детали компании
                    detail = _get_employer_detail(emp_id)
                    if detail and detail.get("open_vacancies", 0) >= min_vacancies:
                        companies.append(detail)

                    time.sleep(0.5)

                if not items:
                    break

                time.sleep(1)

            except Exception as e:
                print(f"[hh.ru] Ошибка: {e}")
                break

    return companies


def _parse_employers_page(html):
    """Парсит список компаний со страницы hh.ru/employers_company"""
    soup = BeautifulSoup(html, "html.parser")
    companies = []

    # Ищем карточки компаний
    cards = soup.find_all("a", href=re.compile(r"/employer/\d+"))

    for card in cards:
        href = card.get("href", "")
        match = re.search(r"/employer/(\d+)", href)
        if match:
            emp_id = match.group(1)
            name = card.get_text(strip=True)
            if name:
                companies.append({"id": emp_id, "name": name})

    return companies


def _get_employer_detail(employer_id):
    """Получает детали компании через hh.ru API (с куками браузерной сессии)"""
    try:
        resp = SESSION.get(
            f"https://api.hh.ru/employers/{employer_id}",
            headers={"Accept": "application/json"},
            timeout=10
        )

        if resp.status_code != 200:
            return None

        d = resp.json()

        size_label = (d.get("size") or {}).get("name", "")
        employee_count = _parse_size(size_label)

        return {
            "id": employer_id,
            "name": d.get("name", ""),
            "site_url": d.get("site_url", ""),
            "hh_url": d.get("alternate_url", ""),
            "industries": [i.get("name", "") for i in d.get("industries", [])],
            "open_vacancies": d.get("open_vacancies", 0),
            "employee_count": employee_count,
            "trusted": d.get("trusted", False),
        }
    except Exception as e:
        print(f"[hh.ru] Детали {employer_id}: {e}")
        return None


def _parse_size(label):
    mapping = {
        "от 1 до 10": 5,
        "от 10 до 50": 30,
        "от 50 до 100": 75,
        "от 100 до 500": 300,
        "от 500 до 1000": 750,
        "более 1000": 2000,
        "from 1 to 10": 5,
        "from 10 to 50": 30,
        "from 50 to 100": 75,
        "from 100 to 500": 300,
        "from 500 to 1000": 750,
        "more than 1000": 2000,
    }
    return mapping.get(label, 0)
