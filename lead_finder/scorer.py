IT_INDUSTRIES = {
    "Информационные технологии", "IT", "Разработка программного обеспечения",
    "Телекоммуникации", "Интернет", "Кибербезопасность",
}

FINANCE_INDUSTRIES = {
    "Банки", "Страхование", "Финансы", "Инвестиции", "Лизинг",
}

GOOD_INDUSTRIES = {
    "Консалтинг", "Реклама и маркетинг", "Маркетинг", "Реклама",
    "Медицина", "Фармацевтика", "Юридические услуги",
    "Недвижимость", "Аудит", "Бухгалтерия",
}


def score(profile):
    s = 0

    # Размер компании
    emp = profile.get("employee_count", 0)
    open_vac = profile.get("open_vacancies", 0)

    if emp >= 500 or open_vac >= 30:
        s += 40
    elif emp >= 100 or open_vac >= 10:
        s += 30
    elif emp >= 50 or open_vac >= 3:
        s += 20
    else:
        s += 5

    # Отрасль
    industries = set(profile.get("industries", []))

    if industries & IT_INDUSTRIES:
        s += 30  # IT = идеальный клиент (сидят весь день)
    elif industries & FINANCE_INDUSTRIES:
        s += 25
    elif industries & GOOD_INDUSTRIES:
        s += 20
    else:
        s += 10

    # Есть сайт — значит компания реальная и активная
    if profile.get("site_url"):
        s += 10

    # Есть телефон — дополнительный плюс
    if profile.get("phone"):
        s += 10

    # Есть email — можно писать напрямую
    if profile.get("emails"):
        s += 10

    # Верифицирована на hh.ru
    if profile.get("trusted"):
        s += 5

    return min(s, 100)
