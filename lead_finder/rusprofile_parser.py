import requests
import time
import re
from bs4 import BeautifulSoup

BASE = "https://www.rusprofile.ru"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.rusprofile.ru/",
}

# ОКВЭД → отрасль. Регион 77 = Москва
OKVED_INDUSTRIES = [
    ("62",    "Информационные технологии"),
    ("63",    "Информационные технологии"),
    ("64",    "Финансы"),
    ("65",    "Страхование"),
    ("69",    "Юридические услуги"),
    ("70",    "Консалтинг"),
    ("73",    "Маркетинг и реклама"),
    ("78",    "Кадровые услуги"),
    ("21",    "Фармацевтика"),
]

MOSCOW_REGION = "77"


def get_companies(pages_per_okved=2):
    companies = []
    seen_keys = set()

    for okved, industry_name in OKVED_INDUSTRIES:
        print(f"[Rusprofile] ОКВЭД {okved}: {industry_name}...")
        found_in_okved = 0

        for page in range(1, pages_per_okved + 1):
            url = f"{BASE}/okved/{okved}"
            params = {"region": MOSCOW_REGION}
            if page > 1:
                params["page"] = page

            try:
                resp = requests.get(
                    url, headers=HEADERS, params=params,
                    timeout=15, allow_redirects=True
                )

                if resp.status_code == 403:
                    print(f"[Rusprofile] Заблокирован (403)")
                    return companies

                if resp.status_code != 200:
                    print(f"[Rusprofile]   HTTP {resp.status_code}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                # Диагностика на первой странице первого ОКВЭД
                if page == 1 and okved == OKVED_INDUSTRIES[0][0]:
                    _print_diagnostics(soup, resp.url)

                items = _extract_companies(soup, industry_name)

                added = 0
                for item in items:
                    key = item.get("inn") or item["name"].lower().strip()
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        companies.append(item)
                        added += 1

                print(f"[Rusprofile]   стр.{page}: {added} компаний")
                found_in_okved += added

                if added == 0:
                    break

                time.sleep(2)

            except Exception as e:
                print(f"[Rusprofile] Ошибка: {e}")
                break

        time.sleep(1)

    print(f"[Rusprofile] Итого: {len(companies)} компаний")
    return companies


def _print_diagnostics(soup, final_url):
    title = soup.title.get_text(strip=True) if soup.title else "нет"
    print(f"[Rusprofile] URL: {final_url}")
    print(f"[Rusprofile] Заголовок: {title}")
    all_links = soup.find_all("a", href=True)
    print(f"[Rusprofile] Всего ссылок: {len(all_links)}")
    id_links = [a["href"] for a in all_links if "/id/" in a.get("href", "")]
    print(f"[Rusprofile] Ссылок /id/: {len(id_links)}")
    for h in id_links[:5]:
        print(f"  {h}")
    if not id_links:
        print("[Rusprofile] Первые 10 ссылок:")
        for a in all_links[:10]:
            print(f"  {a.get('href', '')}")


def _extract_companies(soup, industry_name):
    companies = []

    # Ищем ссылки вида /id/XXXXXXXX — это страницы компаний
    company_links = []
    for a in soup.find_all("a", href=re.compile(r"^/id/\d+")):
        name = a.get_text(strip=True)
        href = a["href"]
        if name and len(name) >= 3:
            company_links.append((name, href))

    for name, href in company_links:
        if _is_skip_name(name):
            continue

        rusprofile_url = BASE + href

        # Пытаемся найти карточку с дополнительными данными
        card = _find_card(soup, a_href=href)

        inn = ""
        phone = None
        address = ""

        if card:
            text = card.get_text(" ", strip=True)
            inn_m = re.search(r"ИНН\s*:?\s*(\d{10,12})", text)
            if inn_m:
                inn = inn_m.group(1)
            phone_m = re.search(
                r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text
            )
            if phone_m:
                phone = phone_m.group(0)
            # Адрес: ищем элемент с Москва
            for el in card.find_all(True):
                t = el.get_text(strip=True)
                if "Москва" in t and 5 < len(t) < 200:
                    address = t
                    break

        companies.append({
            "name": name,
            "inn": inn,
            "phone": phone,
            "site_url": rusprofile_url,
            "address": address,
            "industries": [industry_name],
            "open_vacancies": 0,
            "employee_count": 0,
            "trusted": True,
            "emails": [],
        })

    return companies


def _find_card(soup, a_href):
    """Walk up from the link to find a container card element."""
    link_el = soup.find("a", href=a_href)
    if not link_el:
        return None
    el = link_el.parent
    for _ in range(6):
        if el is None:
            break
        tag = el.name
        if tag in ("li", "article", "section"):
            return el
        cls = " ".join(el.get("class", []))
        if re.search(r"item|card|row|company|result|org", cls, re.I):
            return el
        el = el.parent
    return link_el.parent


_SKIP = {
    "подробнее", "смотреть", "все компании", "раскрыть", "скрыть",
    "следующая", "предыдущая", "войти", "зарегистрироваться",
}


def _is_skip_name(name):
    return name.lower().strip() in _SKIP or len(name) < 3
