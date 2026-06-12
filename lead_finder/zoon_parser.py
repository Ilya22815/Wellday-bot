from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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

            for page in range(1, pages_per_category + 1):
                page_url = base_url if page == 1 else f"{base_url}?page={page}"

                try:
                    driver.get(page_url)
                    time.sleep(4)

                    # Отладка — сохраняем HTML и пушим на GitHub
                    if page == 1 and base_url == CATEGORIES[0][0]:
                        with open("zoon_debug.html", "w", encoding="utf-8") as f:
                            f.write(driver.page_source)
                        print("[Zoon] Сохранил HTML, пушу на GitHub...")
                        import subprocess, os
                        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zoon_debug.html")
                        r1 = subprocess.run(["git", "-C", repo_root, "add", debug_path], capture_output=True, text=True)
                        r2 = subprocess.run(["git", "-C", repo_root, "commit", "-m", "debug: Zoon HTML dump"], capture_output=True, text=True)
                        r3 = subprocess.run(["git", "-C", repo_root, "push", "origin", "claude/code-editing-capability-q77b1y"], capture_output=True, text=True)
                        if r3.returncode == 0:
                            print("[Zoon] HTML на GitHub")
                        else:
                            print(f"[Zoon] Ошибка push: {r3.stderr[:200]}")
                            print(f"[Zoon] add: {r1.returncode}, commit: {r2.returncode}, push: {r3.returncode}")

                    items = _extract_companies(driver, industry)
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
                    print(f"[Zoon] Ошибка на {page_url}: {e}")
                    break

            time.sleep(1)

    finally:
        driver.quit()

    print(f"[Zoon] Найдено: {len(companies)} компаний")
    return companies


def _extract_companies(driver, industry):
    companies = []

    # Пробуем разные селекторы карточек
    cards = []
    for selector in [
        "[class*='company-item']",
        "[class*='CompanyCard']",
        "[class*='service-item']",
        "[class*='place-item']",
        "article",
        "li[class*='company']",
    ]:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards:
            break

    if not cards:
        return companies

    for card in cards:
        try:
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
        except Exception:
            continue

    return companies


def _extract_name(card):
    for selector in ["h2", "h3", "h1", "[class*='title']", "[class*='name']"]:
        try:
            els = card.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                text = el.text.strip()
                if text and len(text) > 2:
                    return text
        except Exception:
            continue
    return None


def _extract_phone(card):
    for selector in ["[class*='phone']", "[class*='tel']", "[itemprop='telephone']"]:
        try:
            els = card.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                text = el.text.strip()
                if re.search(r"\+?[\d\s\-\(\)]{7,}", text):
                    return text
        except Exception:
            continue
    return None


def _extract_site(card):
    for selector in ["[class*='site']", "[class*='web']", "[itemprop='url']"]:
        try:
            els = card.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                href = el.get_attribute("href") or el.text.strip()
                if href and href.startswith("http") and "zoon.ru" not in href:
                    return href
        except Exception:
            continue
    return None


def _extract_address(card):
    for selector in ["[class*='address']", "[class*='addr']", "[itemprop='address']"]:
        try:
            els = card.find_elements(By.CSS_SELECTOR, selector)
            for el in els:
                text = el.text.strip()
                if text:
                    return text
        except Exception:
            continue
    return None
