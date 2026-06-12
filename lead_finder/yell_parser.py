import requests
from bs4 import BeautifulSoup
import time
import re

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Referer": "https://www.yell.ru/",
})

CATEGORIES = [
    ("https://www.yell.ru/moscow/cat/it-kompanii/",                  "Информационные технологии"),
    ("https://www.yell.ru/moscow/cat/razrabotka-po/",               "Разработка программного обеспечения"),
    ("https://www.yell.ru/moscow/cat/banki/",                        "Банки"),
    ("https://www.yell.ru/moscow/cat/strakhovye-kompanii/",          "Страхование"),
    ("https://www.yell.ru/moscow/cat/konsaltingovye-kompanii/",      "Консалтинг"),
    ("https://www.yell.ru/moscow/cat/yuridicheskie-kompanii/",       "Юридические услуги"),
    ("https://www.yell.ru/moscow/cat/marketingovye-agentstva/",      "Маркетинг"),
    ("https://www.yell.ru/moscow/cat/reklamnye-agentstva/",          "Реклама"),
    ("https://www.yell.ru/moscow/cat/kadrovye-agentstva/",           "Кадровые агентства"),
    ("https://www.yell.ru/moscow/cat/farmatsevticheskie-kompanii/",  "Фармацевтика"),
]


def get_companies(pages_per_category=3):
    companies = []
    seen_names = set()

    try:
        SESSION.get("https://www.yell.ru/", timeout=10)
        time.sleep(1)
    except Exception:
        pass

    for base_url, industry in CATEGORIES:
        print(f"[Yell] Категория: {industry}...")

        for page in range(1, pages_per_category + 1):
            page_url = base_url if page == 1 else f"{base_url}?page={page}"
            try:
                resp = SESSION.get(page_url, timeout=12)
                if resp.status_code != 200:
                    print(f"[Yell] Статус {resp.status_code} для {page_url}")
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
                print(f"[Yell] Ошибка: {e}")
                break

        time.sleep(0.5)

    print(f"[Yell] Найдено: {len(companies)} компаний")
    return companies


def _parse_listing(html, industry):
    soup = BeautifulSoup(html, "html.parser")
    companies = []

    # Yell.ru структура карточек
    cards = soup.find_all("div", class_=re.compile(r"company|CompanySnippet|b-company|listing", re.I))
    if not cards:
        cards = soup.find_all("article")
    if not cards:
        cards = soup.find_all("li", class_=re.compile(r"company|item|result", re.I))

    for card in cards:
        name = _extract_name(card)
        if not name or len(name) < 3:
            continue

        phone   = _extract_phone(card)
        site    = _extract_site(card)
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
    for tag in ["h2", "h3", "h1"]:
        el = card.find(tag)
        if el:
            text = el.get_text(strip=True)
            if text and len(text) > 2:
                return text

    el = card.find("a", class_=re.compile(r"name|title|company", re.I))
    if el:
        text = el.get_text(strip=True)
        if text and len(text) > 2:
            return text

    return None


def _extract_phone(card):
    el = card.find(attrs={"itemprop": "telephone"})
    if el:
        return el.get_text(strip=True)

    for attr in ["data-phone", "data-tel", "data-number"]:
        val = card.get(attr)
        if val:
            return val

    el = card.find(class_=re.compile(r"phone|tel", re.I))
    if el:
        text = el.get_text(strip=True)
        if re.search(r"\+?[\d\s\-\(\)]{7,}", text):
            return text.strip()

    return None


def _extract_site(card):
    el = card.find("a", class_=re.compile(r"site|web|url|link", re.I))
    if el:
        href = el.get("href", "")
        if href.startswith("http") and "yell.ru" not in href:
            return href

    el = card.find(attrs={"itemprop": "url"})
    if el:
        return el.get("content") or el.get("href") or el.get_text(strip=True)

    return None


def _extract_address(card):
    el = card.find(attrs={"itemprop": "address"})
    if el:
        return el.get_text(strip=True)

    el = card.find(class_=re.compile(r"address|addr|location", re.I))
    if el:
        return el.get_text(strip=True)

    return None
