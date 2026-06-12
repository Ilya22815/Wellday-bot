import requests
import time

GIS_API = "https://catalog.api.2gis.com/3.0/items"

# Moscow city_id in 2GIS
MOSCOW_CITY_ID = "1"

SEARCH_QUERIES = [
    "IT компания",
    "разработка программного обеспечения",
    "системный интегратор",
    "банк",
    "страховая компания",
    "консалтинговая компания",
    "юридическая компания",
    "аудиторская компания",
    "маркетинговое агентство",
    "рекламное агентство",
    "фармацевтическая компания",
    "медицинская компания",
    "телекоммуникационная компания",
    "финансовая компания",
]


def get_companies(api_key, queries=None, per_page=10):
    if not api_key:
        print("[2GIS] Нет API ключа!")
        return []

    if queries is None:
        queries = SEARCH_QUERIES

    companies = []
    seen_names = set()

    for query in queries:
        print(f"[2GIS] Ищем: {query}...")
        page = 1
        got_any = False

        while True:
            try:
                resp = requests.get(
                    GIS_API,
                    params={
                        "q": query,
                        "city_id": MOSCOW_CITY_ID,
                        "fields": "items.contact_groups,items.address,items.external_content,items.rubrics",
                        "key": api_key,
                        "page_size": per_page,
                        "page": page,
                        "type": "branch",
                        "sort": "relevance",
                    },
                    timeout=10
                )

                if resp.status_code == 403:
                    print("[2GIS] Неверный API ключ!")
                    return companies

                if resp.status_code != 200:
                    print(f"[2GIS] Статус {resp.status_code}: {resp.text[:300]}")
                    break

                try:
                    data = resp.json()
                except Exception as e:
                    print(f"[2GIS] Ошибка JSON: {e}, текст: {resp.text[:200]}")
                    break

                result = data.get("result", {})
                items = result.get("items", [])
                total = result.get("total", 0)

                print(f"[2GIS]   стр.{page}: статус={resp.status_code}, найдено={len(items)}, всего={total}")

                if not items:
                    if not got_any and page == 1:
                        # Print raw response to help diagnose
                        print(f"[2GIS]   Ответ API: {str(data)[:400]}")
                    break

                got_any = True

                if page == 1 and query == queries[0]:
                    print(f"[2GIS]   Поля первой записи: {list(items[0].keys())}")

                for item in items:
                    name = item.get("name", "").strip()
                    if not name or name in seen_names:
                        continue
                    seen_names.add(name)

                    phone = _extract_phone(item)
                    site = _extract_site(item)
                    address = (item.get("address") or {}).get("name", "")
                    rubrics = [r.get("name", "") for r in item.get("rubrics", [])]

                    companies.append({
                        "name": name,
                        "phone": phone,
                        "site_url": site,
                        "address": address,
                        "industries": rubrics,
                        "open_vacancies": 0,
                        "employee_count": 0,
                        "trusted": True,
                        "emails": [],
                    })

                if page * per_page >= min(total, 200):
                    break

                page += 1
                time.sleep(0.3)

            except Exception as e:
                print(f"[2GIS] Ошибка: {e}")
                break

        time.sleep(0.5)

    print(f"[2GIS] Найдено: {len(companies)} компаний")
    return companies


def _extract_phone(item):
    for group in item.get("contact_groups", []):
        for contact in group.get("contacts", []):
            if contact.get("type") == "phone":
                return contact.get("value", "")
    for contact in item.get("contacts", []):
        if contact.get("type") == "phone":
            return contact.get("value", "")
    return None


def _extract_site(item):
    for group in item.get("contact_groups", []):
        for contact in group.get("contacts", []):
            if contact.get("type") == "website":
                url = contact.get("value", "")
                if url and "2gis" not in url:
                    return url
    for contact in item.get("contacts", []):
        if contact.get("type") == "website":
            url = contact.get("value", "")
            if url and "2gis" not in url:
                return url
    for ext in item.get("external_content", []):
        if ext.get("type") == "website":
            return ext.get("url", "")
    return None
