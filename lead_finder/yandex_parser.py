import requests
import time

YANDEX_SEARCH_API = "https://search-maps.yandex.ru/v1/"

# Москва — центральные координаты
MOSCOW_LL  = "37.617633,55.755786"
MOSCOW_SPN = "0.5,0.5"

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


def get_companies(api_key, queries=None, results_per_query=50):
    if not api_key:
        print("[Яндекс] Нет API ключа!")
        return []

    if queries is None:
        queries = SEARCH_QUERIES

    companies = []
    seen_names = set()

    for query in queries:
        print(f"[Яндекс] Ищем: {query}...")
        skip = 0

        while skip < results_per_query:
            try:
                resp = requests.get(
                    YANDEX_SEARCH_API,
                    params={
                        "apikey": api_key,
                        "text": f"{query} Москва",
                        "lang": "ru_RU",
                        "type": "biz",
                        "ll": MOSCOW_LL,
                        "spn": MOSCOW_SPN,
                        "results": 10,
                        "skip": skip,
                    },
                    timeout=10
                )

                if resp.status_code == 403:
                    print("[Яндекс] Неверный API ключ!")
                    return companies

                if resp.status_code != 200:
                    print(f"[Яндекс] Статус: {resp.status_code}")
                    break

                data = resp.json()
                features = data.get("features", [])

                if not features:
                    break

                for feature in features:
                    props = feature.get("properties", {})
                    meta = props.get("CompanyMetaData", {})

                    name = meta.get("name", "").strip()
                    if not name or name in seen_names:
                        continue
                    seen_names.add(name)

                    phone = _extract_phone(meta)
                    site = meta.get("url", "") or ""
                    address = meta.get("address", "")
                    categories = [c.get("name", "") for c in meta.get("Categories", [])]

                    companies.append({
                        "name": name,
                        "phone": phone,
                        "site_url": site,
                        "address": address,
                        "industries": categories,
                        "open_vacancies": 0,
                        "employee_count": 0,
                        "trusted": True,
                        "emails": [],
                    })

                skip += 10
                time.sleep(0.3)

            except Exception as e:
                print(f"[Яндекс] Ошибка: {e}")
                break

        found = len([c for c in companies if c not in companies[:len(companies) - len(companies)]])
        time.sleep(0.5)

    print(f"[Яндекс] Найдено: {len(companies)} компаний")
    return companies


def _extract_phone(meta):
    phones = meta.get("Phones", [])
    for p in phones:
        formatted = p.get("formatted", "")
        if formatted:
            return formatted
    return None
