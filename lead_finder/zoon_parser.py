from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

CATEGORIES = [
    ("https://zoon.ru/moscow/it_outsourcing/",        "Информационные технологии"),
    ("https://zoon.ru/moscow/programming/",           "Разработка программного обеспечения"),
    ("https://zoon.ru/moscow/banks/",                 "Банки"),
    ("https://zoon.ru/moscow/insurance_companies/",   "Страхование"),
    ("https://zoon.ru/moscow/consulting/",            "Консалтинг"),
    ("https://zoon.ru/moscow/lawyers/",               "Юридические услуги"),
    ("https://zoon.ru/moscow/marketing/",             "Маркетинг"),
    ("https://zoon.ru/moscow/advertising_agencies/",  "Реклама"),
    ("https://zoon.ru/moscow/recruitment/",           "Кадровые агентства"),
    ("https://zoon.ru/moscow/pharmaceutics/",         "Фармацевтика"),
]


def _create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def get_companies(pages_per_category=2):
    print("[Zoon] Запускаем браузер...")
    driver = _create_driver()
    companies = []
    seen_names = set()

    try:
        for base_url, industry in CATEGORIES:
            print(f"[Zoon] Категория: {industry}...")
            # Extract the category path for URL-based filtering
            # e.g. "https://zoon.ru/moscow/it_outsourcing/" -> "/moscow/it_outsourcing/"
            category_path = base_url.replace("https://zoon.ru", "").rstrip("/")

            for page in range(1, pages_per_category + 1):
                page_url = base_url if page == 1 else f"{base_url}?page={page}"

                try:
                    driver.get(page_url)
                    time.sleep(5)

                    html = driver.page_source

                    # On first page of first category, print diagnostic info
                    if page == 1 and base_url == CATEGORIES[0][0]:
                        _print_diagnostics(html, category_path)

                    items = _extract_companies_bs4(html, industry, category_path)
                    added = 0
                    for item in items:
                        name = item.get("name", "")
                        if name and name not in seen_names:
                            seen_names.add(name)
                            companies.append(item)
                            added += 1

                    print(f"[Zoon]   стр.{page}: найдено {added} компаний")

                    if added == 0:
                        break

                    time.sleep(1)

                except Exception as e:
                    print(f"[Zoon] Ошибка на {page_url}: {e}")
                    break

            time.sleep(1)

    finally:
        driver.quit()

    print(f"[Zoon] Найдено: {len(companies)} компаний")
    return companies


def _print_diagnostics(html, category_path):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.text if soup.title else "нет"
    print(f"[Zoon] Заголовок страницы: {title}")

    # Count links matching company URL pattern
    pattern = re.compile(r"^https://zoon\.ru" + re.escape(category_path) + r"/[^/?#]+")
    matching = [a["href"] for a in soup.find_all("a", href=True) if pattern.match(a["href"])]
    print(f"[Zoon] Ссылок на компании найдено: {len(matching)}")

    # Show first 2000 chars of HTML for debugging
    print(f"[Zoon] === НАЧАЛО HTML ===")
    print(html[:2000])
    print(f"[Zoon] === КОНЕЦ HTML (показаны первые 2000 символов из {len(html)}) ===")


def _extract_companies_bs4(html, industry, category_path):
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    seen_hrefs = set()

    # Strategy: find all <a> links pointing to company detail pages
    # Zoon company URLs look like: https://zoon.ru/moscow/it_outsourcing/some-company/
    pattern = re.compile(r"^https://zoon\.ru" + re.escape(category_path) + r"/[^/?#]+/?$")

    company_links = [a for a in soup.find_all("a", href=True) if pattern.match(a["href"])]

    for link in company_links:
        href = link["href"].rstrip("/")
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        # The company name is the link text, or text of a heading inside the link
        name = link.get_text(strip=True)
        if not name or len(name) < 3:
            continue

        # Walk up to find a card container that has phone/address
        container = link.parent
        for _ in range(4):
            if container is None:
                break
            text = container.get_text(" ", strip=True)
            if re.search(r"\+?[\d][\d\s\-\(\)]{6,}", text):
                break
            container = container.parent

        phone = _find_phone(container) if container else None
        address = _find_address(container) if container else None

        companies.append({
            "name": name,
            "phone": phone,
            "site_url": None,
            "address": address,
            "industries": [industry],
            "open_vacancies": 0,
            "employee_count": 0,
            "trusted": True,
            "emails": [],
        })

    return companies


def _find_phone(tag):
    if tag is None:
        return None
    text = tag.get_text(" ", strip=True)
    m = re.search(r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text)
    if m:
        return m.group(0)
    m = re.search(r"\+?[\d][\d\s\-\(\)]{9,14}", text)
    if m:
        return m.group(0).strip()
    return None


def _find_address(tag):
    if tag is None:
        return None
    # Look for itemprop=address first
    el = tag.find(attrs={"itemprop": "address"})
    if el:
        return el.get_text(strip=True)
    # Look for class containing 'address' or 'addr'
    for el in tag.find_all(True):
        cls = " ".join(el.get("class", []))
        if re.search(r"address|addr|location", cls, re.I):
            text = el.get_text(strip=True)
            if text:
                return text
    return None
