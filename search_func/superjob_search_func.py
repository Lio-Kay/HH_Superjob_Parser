import logging as log
import pathlib as pl

from forex_python.converter import CurrencyRates
from inspect import currentframe
from search_func.search_navigation import get_vacancies_navigation, get_companies_navigation

from db_func.db_manipulation_func import DBManager


log.basicConfig(level=log.DEBUG, filename=pl.Path.cwd() / 'project_logs.log', filemode='w')


converter = CurrencyRates()


def get_vacancies_superjob(SuperJobAPI, superjob_vac_params):
    """
    Основная логика поиска вакансий от superjob.ru API
    :param SuperJobAPI: Класс для работы c API superjob.ru
    :param superjob_vac_params: Параметры для поиска вакансий superjob.ru
    """
    first_vacancy_request: dict = SuperJobAPI.get_vacancies(superjob_vac_params)
    if first_vacancy_request.get('error'):
        print(f'Ошибка {first_vacancy_request.get("error").get("message")}')
        return
    if first_vacancy_request.get('total') == 0:
        print('Вакансии не найдены')
        return
    print(f'Найдено {first_vacancy_request.get("total")} компаний')
    for page in range(first_vacancy_request.get("total")):
        # Увеличиваем параметр страница на 1
        superjob_vac_params.page = page
        vacancy: dict = SuperJobAPI.get_vacancies(superjob_vac_params)
        vac_id: int = vacancy.get('objects', [])[0].get('id')
        # Проверяем на наличие вакансии в ЧС
        if DBManager.check_blacklisted_vacancies(vac_id=vac_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_vacancy_in_db(vac_id=vac_id):
            continue
        emp_id: int = vacancy.get('objects', [])[0].get('id_client')
        employer: dict = SuperJobAPI.get_employer_by_id(emp_id)
        vac_name: str = vacancy.get('objects', [])[0].get('profession')
        print(employer)
        emp_name: str = employer.get('title')
        emp_industries: str = employer.get('industry', [])
        emp_industry: list = []
        for industry in emp_industries:
            emp_industry.append(industry.get('title'))
        emp_industry: str = ', '.join(emp_industry)
        emp_vac_count: int = employer.get('vacancy_count')
        vac_pay_from: int or str = vacancy.get('objects', [])[0].get('payment_from', 0)
        vac_pay_to: int or str = vacancy.get('objects', [])[0].get('payment_to', 0)
        if vac_pay_to and vac_pay_from:
            vac_pay: int = int((vac_pay_to + vac_pay_from) / 2)
        elif vac_pay_to == 0:
            vac_pay: int = vac_pay_from
        else:
            vac_pay: int = 0
        try:
            vac_pay_curr: str or None = vacancy.get('objects', [])[0].get('currency')
        except AttributeError:
            vac_pay_curr: str = 'RUB'
        # Переводим зп в рубли
        if vac_pay_curr == 'USD' and vac_pay is not None:
            vac_pay: int = converter.convert('USD', 'RUB', vac_pay)
            vac_pay_curr: str = 'RUB'
        elif vac_pay_curr == 'EUR' and vac_pay is not None:
            vac_pay: int = converter.convert('EUR', 'RUB', vac_pay)
            vac_pay_curr: str = 'RUB'
        elif vac_pay_curr == 'KZT' and vac_pay is not None:
            vac_pay: int = converter.convert('KZT', 'RUB', vac_pay)
            vac_pay_curr: str = 'RUB'
        else:
            vac_pay_curr: str = 'RUB'
        vac_employer: str = vacancy.get('objects', [])[0].get('firm_name')
        # Адрес не всегда указан полностью, ловим ошибки
        vac_area: dict or str = vacancy.get('objects', [])[0].get('address', 'Не указан')
        if vac_area is None:
            vac_area: str = 'Не указан'
        try:
            vac_schedule: str or None = vacancy.get('objects', [])[0].get('type_of_work').get('title')
        except AttributeError:
            vac_schedule: str or None = None
        vac_requirement: str = vacancy.get('objects', [])[0].get('candidat', 'Не указанны')
        vac_responsibility: str = vacancy.get('objects', [])[0].get('work', 'Не указанны')
        if vac_responsibility is None:
            vac_responsibility = 'Не указанны'
        if vac_requirement is None:
            vac_requirement = 'Не указанны'
        vac_url: str = vacancy.get('objects', [])[0].get('link')
        emp_url: str = employer.get('link')
        # Делаем вывод красивым
        if vac_pay_curr == 'RUR':
            vac_pay_curr: str = 'Руб'
        vac_pay_gross = False

        print(
            f'---\033[1mВакансия №{page+1} из {first_vacancy_request.get("total")}\033[0m---\n'
            f'ID: {vac_id}. Название: {vac_name}. Заработная плата '
            f'от: {vac_pay_from}, до {vac_pay_to} {vac_pay_curr}.\n'
            f'Компания: {vac_employer}. Адрес: {vac_area}.\n'
            f'Обязанности: {vac_responsibility}.\n'
            f'Требования: {vac_requirement}.\n'
            f'Ссылка на вакансию: {vac_url}')

        # Выводим окно с выбором дальнейших действий
        user_choice: int = get_vacancies_navigation()
        # Сохранить в файл и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=emp_id, name=emp_name, industry=emp_industry,
                                          vac_count=emp_vac_count, url=emp_url)
            DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=emp_id, name=vac_name, area=vac_area,
                                         salary=vac_pay, currency=vac_pay_curr, gross=vac_pay_gross,
                                         schedule=vac_schedule,
                                         requirement=vac_requirement, responsibility=vac_responsibility,
                                         url=vac_url)
        # Добавить в ЧС
        elif user_choice == 2:
            DBManager.blacklist_vacancy(vac_id=vac_id)
        # Пропустить вакансию
        elif user_choice == 3:
            continue
        # Закончить работу с API superjob.ru
        elif user_choice == 4:
            return


def get_employers_superjob(SuperJobAPI, superjob_params):
    """
    Основная логика поиска компаний от superjob.ru API
    :param SuperJobAPI: Класс для работы c API superjob.ru
    :param superjob_params: Параметры для поиска вакансий superjob.ru
    """
    # Делаем первый запрос для получения кол-ва найденных компаний
    first_company_request: dict = SuperJobAPI.get_employers_by_keywords(superjob_params)
    if first_company_request.get('errors'):
        print(f'Ошибка {first_company_request.get("errors")[0].get("type")}')
        return
    if first_company_request['found'] == 0:
        print('Найдено 0 компаний')
        return
    print(f'Найдено {first_company_request["found"]} компаний')
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 компания на страницу)
    for page in range(0, first_company_request['found']):
        superjob_params.page = page
        emp: dict = HH_API.get_employers_by_keywords(hh_emp_params())
        emp_id: int = int(emp.get('items', [])[0].get('id'))
        # Проверяем ЧС
        if DBManager.check_blacklisted_employer(emp_id=emp_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_employer_in_db(emp_id=emp_id):
            continue
        employer: dict = HH_API.get_employer_by_id(emp_id)
        emp_industries: str = employer.get('industries', [])
        emp_industry: list = []
        for industry in emp_industries:
            emp_industry.append(industry.get('name'))
        emp_industry: str = ' ,'.join(emp_industry)
        emp_name: str = emp.get('items', [])[0].get('name')
        emp_vac_count: int = employer.get('open_vacancies')
        emp_url: str = emp.get('items', [])[0].get('alternate_url')

        print(
            f'---\033[1mКомпания №{page + 1} из {first_company_request["found"]}\033[0m---\n'
            f'ID: {emp_id}. Название: {emp_name}.'
            f'Сфера деятельности: {emp_industry}.'
            f'Кол-во вакансий компании: {emp_vac_count}. Ссылка на компанию: {emp_url}')

        # Выводим окно с выбором дальнейших действий
        user_choice: int = get_vacancies_navigation()
        # Сохранить в файл и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=emp_id, name=emp_name, industry=emp_industry,
                                          vac_count=emp_vac_count, url=emp_url)
            save_user_choice = input('Сохранить все вакансии копании в файл?\n'
                                     '1 - Да\n2 - Нет (по умолчанию)\n')
            if save_user_choice == '1':
                if emp_vac_count == 0:
                    print('У компании нет активных вакансий')
                else:
                    for vacancy_num in range(emp_vac_count):
                        save_vacancy_by_id(vacancy_num=vacancy_num, emp_id=emp_id, SuperjobAPI=SuperJobAPI)
        # Добавить в ЧС
        elif user_choice == 2:
            DBManager.blacklist_employer(emp_id=emp_id)
        # Пропустить вакансию
        elif user_choice == 3:
            pass
        # Закончить работу с API superjob.ru
        elif user_choice == 4:
            return


def save_vacancy_by_id(vacancy_num: int, emp_id: int, SuperjobAPI) -> None:
    """
    :param vacancy_num: Порядковый номер вакансии для for loop
    :param emp_id: ID компании
    :param SuperjobAPI: Класс для API запросов
    """
    search_params: dict = {'page': vacancy_num,
                           'per_page': 1,
                           'id_client': emp_id}
    vacancy = SuperjobAPI.get_vacancies(search_params)
    vac_id: int = int(vacancy.get('items', [])[0].get('id'))
    vac_name: str = vacancy.get('items', [])[0].get('name')
    # Адрес не всегда указан полностью, ловим ошибки
    try:
        vac_employer_raw_loc: dict = vacancy.get("items", [])[0].get("address")
        vac_area: str = f'{vac_employer_raw_loc.get("city")}, {vac_employer_raw_loc.get("street")} ' \
                        f'{vac_employer_raw_loc.get("building")}'
        if vac_area == 'None None None':
            try:
                vac_area: str = \
                    f'{vacancy.get("items", [])[0].get("address").get("metro").get("station_name")}'
            except Exception:
                vac_area: str = 'Не указан'
    except AttributeError:
        vac_area: str = vacancy.get('items', [])[0].get('area').get('name')
    # Ловим ошибки с зп
    try:
        vac_pay_from: int = vacancy.get('items', [])[0].get('salary', []).get('from', 0)
    except AttributeError:
        vac_pay_from: int = 0
    try:
        vac_pay_to: int = vacancy.get('items', [])[0].get('salary', []).get('to', 0)
    except AttributeError:
        vac_pay_to: int = 0
    # Выбираем зп для сохранения в ДБ
    if vac_pay_from and vac_pay_to:
        vac_pay: int = int((vac_pay_to + vac_pay_from) / 2)
    elif vac_pay_to:
        vac_pay: int = vac_pay_to
    elif vac_pay_from:
        vac_pay: int = vac_pay_from
    else:
        vac_pay: int = 0
    try:
        vac_pay_curr: str or None = vacancy.get('items', [])[0].get('salary').get('currency')
    except AttributeError:
        vac_pay_curr: str = 'RUB'
    # Переводим зп в рубли
    if vac_pay_curr == 'USD' and vac_pay is not None:
        vac_pay: int = converter.convert('USD', 'RUB', vac_pay)
        vac_pay_curr: str = 'RUB'
    elif vac_pay_curr == 'EUR' and vac_pay is not None:
        vac_pay: int = converter.convert('EUR', 'RUB', vac_pay)
        vac_pay_curr: str = 'RUB'
    elif vac_pay_curr == 'KZT' and vac_pay is not None:
        vac_pay: int = converter.convert('KZT', 'RUB', vac_pay)
        vac_pay_curr: str = 'RUB'
    else:
        vac_pay_curr: str = 'RUB'
    try:
        vac_pay_gross: bool or None = vacancy.get('items', [])[0].get('salary').get('gross')
    except AttributeError:
        vac_pay_gross: bool = False
    try:
        vac_schedule: str or None = vacancy.get('items', [])[0].get('employment', None).get('name', None)
    except AttributeError:
        vac_schedule: str or None = None
    vac_requirement: str = vacancy.get('items', [])[0].get('snippet').get('requirement', None)
    vac_responsibility: str = vacancy.get('items', [])[0].get('snippet').get('responsibility', None)
    vac_url: str = vacancy.get('items', [])[0].get('alternate_url')

    DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=emp_id, name=vac_name, area=vac_area,
                                 salary=vac_pay, currency=vac_pay_curr, gross=vac_pay_gross,
                                 schedule=vac_schedule,
                                 requirement=vac_requirement, responsibility=vac_responsibility,
                                 url=vac_url)
