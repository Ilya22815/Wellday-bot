import re
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PRIORITY_PREFIXES = ["hr", "job", "career", "рекрутинг", "info", "contact", "office"]


def find_emails_on_site(site_url, timeout=8):
    """
    Парсит сайт компании и ищет email-адреса.
    Приоритет — hr@, job@, info@.
    """
    if not site_url:
        return []

    if not site_url.startswith("http"):
        site_url = "https://" + site_url

    emails = set()

    for path in ["", "/contacts", "/contact", "/about", "/company", "/ru/contacts"]:
        try:
            resp = requests.get(
                site_url.rstrip("/") + path,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True
            )
            if resp.status_code == 200:
                found = EMAIL_RE.findall(resp.text)
                for e in found:
                    e = e.lower().strip(".,;")
                    if _is_valid_email(e):
                        emails.add(e)
        except Exception:
            pass

    return _sort_by_priority(list(emails))


def generate_email_patterns(company_name, site_url=""):
    """
    Генерирует вероятные email-адреса по шаблонам.
    Используется если сайт не дал реальных адресов.
    """
    domain = _extract_domain(site_url) if site_url else _name_to_domain(company_name)
    if not domain:
        return []

    patterns = [
        f"hr@{domain}",
        f"info@{domain}",
        f"job@{domain}",
        f"office@{domain}",
        f"contact@{domain}",
    ]
    return patterns


def _extract_domain(url):
    url = url.replace("https://", "").replace("http://", "").split("/")[0]
    return url if "." in url else None


def _name_to_domain(name):
    domain = name.lower()
    domain = re.sub(r"[^\w]", "", domain)
    return f"{domain}.ru" if domain else None


def _is_valid_email(email):
    if len(email) > 80:
        return False
    bad = [".png", ".jpg", ".gif", ".svg", "example.com", "domain.ru", "email.ru",
           "yourcompany", "test@", "noreply", "no-reply"]
    return not any(b in email for b in bad)


def _sort_by_priority(emails):
    def priority(e):
        for i, prefix in enumerate(PRIORITY_PREFIXES):
            if e.startswith(prefix):
                return i
        return len(PRIORITY_PREFIXES)
    return sorted(emails, key=priority)
