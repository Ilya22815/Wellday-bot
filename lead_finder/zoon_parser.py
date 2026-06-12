import requests
from bs4 import BeautifulSoup
import time
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://zoon.ru/",
})

CATEGORIES = [
    ("https://zoon.ru/moscow/it_outsourcing/",         "Информационные технологии"),
    ("https://zoon.ru/moscow/programming/",            "Разработка программного обеспечения"),
    ("https://zoon.ru/moscow/banks/",                  "Банки"),
    ("https://zoon.ru/moscow/insurance_companies/",    "Страхование"),
    ("https://zoon.ru/moscow/consulting/",             "Консалтинг"),
    ("https://zoon.ru/moscow/lawyers/",                "Юридические услуги"),
    ("https://zoon.ru/moscow/marketing/",              "Маркетинг"),
    ("https://zoon.ru/moscow/advertising_agencies/",   "Реклама"),
    ("https://zoon.ru/moscow/recruitment/",            "Кадровые агентства"),
    ("https://zoon.ru/moscow/pharmaceutics/",          "Фармацевтика"),
]


def get_companies(pages_per_category=3):
    companies = []
    seen_names = set()

    try:
        SESSION.get("https://zoon.ru/moscow/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    for url, industry in CATEGORIES:
        print(f"[Zoon] Категория: {industry}...")

        for page in range(1, pages_per_category + 1):
            page_url = url if page == 1 else f"{url}?page={page}"
            try:
                resp = SESSION.get(page_url, timeout=12)
                if resp.status_code != 200:
                    break

                items = _parse_listing(resp.text, industry)
                added = 0
                for item in items:
                    name = item.get("name", "")
                    if name and name not in seen_names:
                        seen_names.add(name)
                        companies.append(item)
                        added += 1

                if added == 0:
                    break

                time.sleep(1)

            except Exception as e:
                print(f"[Zoon] Ошибка: {e}")
                break

        time.sleep(0.5)

    print(f"[Zoon] Найдено: {len(companies)} компаний")
    return companies


def _parse_listing(html, industry):
    soup = BeautifulSoup(html, "html.parser")
    companies = []

    cards = (
        soup.find_all("div", class_=re.compile(r"company-item|b-company|service-item|place-item", re.I)) or
        soup.find_all("article") or
        soup.find_all("li", class_=re.compile(r"company|service|place", re.I))
    )

    for card in cards:
        name = _extract_name(card)
        if not name:
            continue

        phone = _extract_phone(card)
        site = _extract_site(card)
        address = _extract_address(card)

        companies.append({
            "name": name,
            "phone": phone,
            "site_url": site,
            "address": address,
            "industries": [industry],
            "open_vacancies": 0,
            "employee_count": 0,
            "trusted": True,
            "emails": [],
        })

    return companies


def _extract_name(card):
    for selector in [
        {"class": re.compile(r"title|name|heading", re.I)},
        {"itemprop": "name"},
    ]:
        el = card.find(["h1", "h2", "h3", "h4", "a"], attrs=selector)
        if el:
            text = el.get_text(strip=True)
            if text and len(text) > 2:
                return text

    a = card.find("a", href=re.compile(r"/moscow/"))
    if a:
        text = a.get_text(strip=True)
        if text and len(text) > 2:
            return text

    return None


def _extract_phone(card):
    el = card.find(attrs={"itemprop": "telephone"})
    if el:
        return el.get_text(strip=True)

    el = card.find(class_=re.compile(r"phone|tel", re.I))
    if el:
        text = el.get_text(strip=True)
        if re.search(r"\+?[\d\s\-\(\)]{7,}", text):
            return text.strip()

    data_phone = card.get("data-phone") or card.get("data-tel")
    if data_phone:
        return data_phone

    return None


def _extract_site(card):
    el = card.find(attrs={"itemprop": "url"})
    if el:
        return el.get("href") or el.get("content") or el.get_text(strip=True)

    el = card.find("a", class_=re.compile(r"site|web|url", re.I))
    if el and el.get("href", "").startswith("http"):
        return el["href"]

    return None


def _extract_address(card):
    el = card.find(attrs={"itemprop": "address"})
    if el:
        return el.get_text(strip=True)

    el = card.find(class_=re.compile(r"address|addr", re.I))
    if el:
        return el.get_text(strip=True)

    return None
