import requests
import time

GIS_API = "https://catalog.api.2gis.com/3.0/items"

# Категории 2GIS, которые нас интересуют
TARGET_RUBRICS = [
    "Информационные технологии",
    "Банки",
    "Страхование",
    "Консалтинг",
    "Реклама и маркетинг",
    "Фармацевтика",
    "Юридические услуги",
    "Бухгалтерские услуги",
    "Недвижимость",
    "Медицина",
]


def get_phone_by_name(company_name, api_key):
    """
    Ищет телефон компании через 2GIS по названию.
    Нужен бесплатный API-ключ: dev.2gis.ru
    """
    if not api_key:
        return None
    try:
        resp = requests.get(
            GIS_API,
            params={
                "q": company_name,
                "fields": "items.contact_groups",
                "region_id": "1",  # Москва
                "key": api_key,
                "page_size": 1,
            },
            timeout=8
        )
        if resp.status_code != 200:
            return None

        items = resp.json().get("result", {}).get("items", [])
        if not items:
            return None

        contacts = items[0].get("contact_groups", [])
        for group in contacts:
            for contact in group.get("contacts", []):
                if contact.get("type") == "phone":
                    return contact.get("value")
        return None

    except Exception:
        return None


def search_companies_by_rubric(rubric, api_key, city_id="1", per_page=20):
    """
    Ищет компании Москвы по рубрике 2GIS.
    Возвращает список с названием, телефоном, адресом.
    """
    if not api_key:
        return []

    try:
        resp = requests.get(
            GIS_API,
            params={
                "q": rubric,
                "fields": "items.contact_groups,items.address",
                "region_id": city_id,
                "key": api_key,
                "page_size": per_page,
                "type": "branch",
            },
            timeout=10
        )
        if resp.status_code != 200:
            return []

        results = []
        items = resp.json().get("result", {}).get("items", [])

        for item in items:
            name = item.get("name", "")
            address = item.get("address", {}).get("name", "")

            phone = None
            contacts = item.get("contact_groups", [])
            for group in contacts:
                for contact in group.get("contacts", []):
                    if contact.get("type") == "phone":
                        phone = contact.get("value")
                        break
                if phone:
                    break

            results.append({
                "name": name,
                "phone": phone,
                "address": address,
            })
            time.sleep(0.1)

        return results

    except Exception as e:
        print(f"[2GIS] Ошибка: {e}")
        return []
