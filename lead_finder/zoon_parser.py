from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import time
import re
import random

CATEGORIES = [
    ("https://zoon.ru/msk/internet/",                    "Информационные технологии"),
    ("https://zoon.ru/msk/banks/",                       "Банки"),
    ("https://zoon.ru/msk/law/",                         "Юридические услуги"),
    ("https://zoon.ru/msk/business/",                    "Консалтинг и бизнес-услуги"),
    ("https://zoon.ru/msk/drugstore/",                   "Фармацевтика"),
    ("https://zoon.ru/msk/insurance/",                   "Страхование"),
    ("https://zoon.ru/msk/marketing/",                   "Маркетинг"),
    ("https://zoon.ru/msk/advertising_agencies/",        "Реклама"),
    ("https://zoon.ru/msk/recruitment/",                 "Кадровые агентства"),
]

ZOON_BASE = "https://zoon.ru"

REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


def _fetch_with_requests(url, category_path, timeout=15):
    """Try fetching the page with plain requests (no browser). Returns html or None."""
    try:
        resp = requests.get(url, headers=REQUESTS_HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None
        html = resp.text
        # Check if we actually got company links (not a captcha/block page)
        if category_path.split("/")[-1] not in html and len(html) < 5000:
            return None
        companies = _extract_companies_bs4(html, "", category_path)
        if companies:
            return html
        return None
    except Exception:
        return None


def _create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def _wait_for_companies(driver, category_path, timeout=8):
    xpath = f"//a[contains(@href, '{category_path}/')]"
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except TimeoutException:
        return False


def get_companies(pages_per_category=2):
    # First, check if Zoon is reachable via plain requests (faster, no bot detection)
    test_url = CATEGORIES[0][0]
    test_path = test_url.replace(ZOON_BASE, "").rstrip("/")
    print("[Zoon] Проверяем доступность через requests...")
    use_requests = _fetch_with_requests(test_url, test_path) is not None

    if use_requests:
        print("[Zoon] Zoon доступен через requests — работаем без браузера (быстрее).")
        return _get_companies_requests(pages_per_category)
    else:
        print("[Zoon] requests не дал результат — запускаем браузер...")
        return _get_companies_selenium(pages_per_category)


def _get_companies_requests(pages_per_category):
    companies = []
    seen_names = set()

    for base_url, industry in CATEGORIES:
        print(f"[Zoon] Категория: {industry}...")
        category_path = base_url.replace(ZOON_BASE, "").rstrip("/")

        for page in range(1, pages_per_category + 1):
            page_url = base_url if page == 1 else f"{base_url}?page={page}"

            html = _fetch_with_requests(page_url, category_path)
            if html is None:
                print(f"[Zoon]   стр.{page}: нет ответа")
                break

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

            time.sleep(random.uniform(1.5, 3.0))

        time.sleep(random.uniform(1.0, 2.0))

    print(f"[Zoon] Найдено: {len(companies)} компаний")
    return companies


def _get_companies_selenium(pages_per_category):
    driver = _create_driver()
    companies = []
    seen_names = set()

    try:
        for base_url, industry in CATEGORIES:
            print(f"[Zoon] Категория: {industry}...")
            category_path = base_url.replace(ZOON_BASE, "").rstrip("/")

            for page in range(1, pages_per_category + 1):
                page_url = base_url if page == 1 else f"{base_url}?page={page}"

                html = None
                for attempt in range(3):
                    try:
                        driver.get(page_url)
                        html = driver.page_source
                        break
                    except WebDriverException as e:
                        err_msg = str(e)
                        if "Timed out receiving message from renderer" in err_msg or "timeout" in err_msg.lower():
                            # Page loaded but JS took too long — grab whatever HTML is there
                            try:
                                html = driver.page_source
                                if html and len(html) > 5000:
                                    print(f"[Zoon]   JS-таймаут, но HTML получен ({len(html)} байт)")
                                    break
                            except Exception:
                                pass
                            print(f"[Zoon] Рендер завис (попытка {attempt+1}/3), жду 15с...")
                            time.sleep(15)
                        elif "ERR_CONNECTION_TIMED_OUT" in err_msg or "ERR_CONNECTION_REFUSED" in err_msg:
                            wait_sec = (attempt + 1) * 20
                            print(f"[Zoon] Нет соединения (попытка {attempt+1}/3), жду {wait_sec}с...")
                            time.sleep(wait_sec)
                        else:
                            print(f"[Zoon] Ошибка на {page_url}: {err_msg[:120]}")
                            break

                if not html or len(html) < 5000:
                    print(f"[Zoon] Пропускаю {page_url} — не удалось получить страницу")
                    break

                try:
                    _wait_for_companies(driver, category_path)

                    if page == 1 and base_url == CATEGORIES[0][0]:
                        print(f"[Zoon] Текущий URL после загрузки: {driver.current_url}")
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

                    time.sleep(random.uniform(2.5, 5.0))

                except Exception as e:
                    print(f"[Zoon] Ошибка обработки {page_url}: {e}")
                    break

            time.sleep(random.uniform(2.0, 4.0))

    finally:
        driver.quit()

    print(f"[Zoon] Найдено: {len(companies)} компаний")
    return companies


def _print_diagnostics(html, category_path):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.text.strip() if soup.title else "нет"
    print(f"[Zoon] Заголовок страницы: {title}")

    all_links = soup.find_all("a", href=True)
    print(f"[Zoon] Всего ссылок: {len(all_links)}")

    cat_hrefs = [a["href"] for a in all_links if category_path in a.get("href", "")]
    print(f"[Zoon] Ссылок содержащих '{category_path}': {len(cat_hrefs)}")
    for href in cat_hrefs[:20]:
        print(f"  {href}")

    if not cat_hrefs:
        print("[Zoon] Первые 15 любых ссылок на странице:")
        for a in all_links[:15]:
            print(f"  {a.get('href', '(нет href)')}")


def _normalize_href(href, category_path):
    if not href:
        return None
    abs_pat = re.compile(
        r"^https://zoon\.ru" + re.escape(category_path) + r"/[^/?#]+/?$"
    )
    rel_pat = re.compile(
        r"^" + re.escape(category_path) + r"/[^/?#]+/?$"
    )
    if abs_pat.match(href):
        return href.rstrip("/")
    if rel_pat.match(href):
        return (ZOON_BASE + href).rstrip("/")
    return None


SKIP_NAMES = {
    "смотреть больше", "читать отзывы", "все отзывы", "показать телефон",
    "записаться", "на карте", "позвонить", "подробнее", "написать",
    "сайт", "отзывы", "фото", "цены", "акции", "контакты",
}


def _extract_companies_bs4(html, industry, category_path):
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    seen_hrefs = set()

    for link in soup.find_all("a", href=True):
        norm = _normalize_href(link["href"], category_path)
        if not norm or norm in seen_hrefs:
            continue

        if any(x in norm for x in ["/reviews/", "/photo/", "/prices/", "/metro/", "/type/"]):
            continue

        name = link.get_text(strip=True)
        if not name or len(name) < 3:
            continue
        if name.lower() in SKIP_NAMES:
            continue

        seen_hrefs.add(norm)

        container = link.parent
        for _ in range(5):
            if container is None:
                break
            if re.search(r"\+?[\d][\d\s\-\(\)]{6,}", container.get_text(" ", strip=True)):
                break
            container = container.parent

        phone = _find_phone(container) if container else None
        address = _find_address(container) if container else None

        companies.append({
            "name": name,
            "phone": phone,
            "site_url": norm,
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
    return None


def _find_address(tag):
    if tag is None:
        return None
    el = tag.find(attrs={"itemprop": "address"})
    if el:
        return el.get_text(strip=True)
    for el in tag.find_all(True):
        cls = " ".join(el.get("class", []))
        if re.search(r"address|addr|location", cls, re.I):
            text = el.get_text(strip=True)
            if text:
                return text
    return None
