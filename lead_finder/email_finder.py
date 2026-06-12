import re
import requests
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
MAILTO_RE = re.compile(r'mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
PRIORITY_PREFIXES = ["hr", "job", "career", "recruit", "work", "info", "contact", "office", "mail", "hello"]

CONTACT_PATHS = [
    "/contacts", "/contact", "/kontakty", "/kontakt",
    "/about", "/o-nas", "/o-kompanii", "/about-us", "/about-company",
    "/company", "/kompaniya",
    "/ru/contacts", "/ru/contact", "/ru/kontakty",
    "/en/contacts", "/en/contact",
    "/pages/contacts", "/pages/contact",
    "/info", "/information",
    "/team", "/komanda",
]


def find_emails_on_site(site_url, timeout=8):
    if not site_url:
        return []

    if not site_url.startswith("http"):
        site_url = "https://" + site_url

    site_url = site_url.rstrip("/")
    emails = set()

    # Проверяем главную страницу и контактные страницы
    pages_to_check = [""] + CONTACT_PATHS

    for path in pages_to_check:
        try:
            resp = requests.get(
                site_url + path,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True
            )
            if resp.status_code != 200:
                continue

            text = resp.text

            # Ищем mailto: ссылки (самые надёжные)
            for e in MAILTO_RE.findall(text):
                e = e.lower().strip(".,;")
                if _is_valid_email(e):
                    emails.add(e)

            # Ищем email в тексте страницы
            for e in EMAIL_RE.findall(text):
                e = e.lower().strip(".,;")
                if _is_valid_email(e):
                    emails.add(e)

            # Если нашли — достаточно, не идём дальше
            if emails:
                break

        except Exception:
            continue

    # Если на главной и контактных не нашли — ищем ссылку на страницу контактов
    if not emails:
        try:
            resp = requests.get(site_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                contact_links = _find_contact_links(resp.text, site_url)
                for link in contact_links[:3]:
                    try:
                        r2 = requests.get(link, headers=HEADERS, timeout=timeout, allow_redirects=True)
                        if r2.status_code == 200:
                            for e in MAILTO_RE.findall(r2.text):
                                e = e.lower().strip(".,;")
                                if _is_valid_email(e):
                                    emails.add(e)
                            for e in EMAIL_RE.findall(r2.text):
                                e = e.lower().strip(".,;")
                                if _is_valid_email(e):
                                    emails.add(e)
                    except Exception:
                        continue
        except Exception:
            pass

    return _sort_by_priority(list(emails))


def _find_contact_links(html, base_url):
    contact_keywords = ["контакт", "contact", "о нас", "about", "связ", "реквизит"]
    links = re.findall(r'href=["\']([^"\']+)["\']', html)
    result = []
    for link in links:
        link_lower = link.lower()
        if any(kw in link_lower for kw in contact_keywords):
            if link.startswith("http"):
                result.append(link)
            elif link.startswith("/"):
                parsed = urlparse(base_url)
                result.append(f"{parsed.scheme}://{parsed.netloc}{link}")
    return result


def _extract_domain(url):
    url = url.replace("https://", "").replace("http://", "").split("/")[0]
    return url if "." in url else None


def _is_valid_email(email):
    if len(email) > 80 or len(email) < 6:
        return False
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$", email):
        return False
    bad = [
        ".png", ".jpg", ".gif", ".svg", ".css", ".js", ".woff",
        "example.com", "domain.ru", "yourcompany", "test@",
        "noreply", "no-reply", "sentry", "email@email",
        "user@", "name@", "mail@mail",
    ]
    return not any(b in email for b in bad)


def _sort_by_priority(emails):
    def priority(e):
        for i, prefix in enumerate(PRIORITY_PREFIXES):
            if e.startswith(prefix + "@"):
                return i
        return len(PRIORITY_PREFIXES)
    return sorted(emails, key=priority)
