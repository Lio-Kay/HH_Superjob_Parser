"""
Этот файл содержит в себе функции для получения данных от hh.ru,
используя функции API запросов в api_requests.py.
"""

import logging as log
import pathlib as pl
from inspect import currentframe
from forex_python.converter import CurrencyRates

from db_func.db_manipulation_func import DBManager
from search_func.search_navigation import get_vacancies_navigation, get_employers_navigation

log.basicConfig(level=log.DEBUG,
                filename=pl.Path.cwd() / 'project_logs.log', filemode='w')

converter = CurrencyRates()


def get_vacancies_hh(HH_api, hh_vac_params) -> None:
    """
    Основная логика поиска вакансий от hh.ru API.
    :param HH_api: Класс для работы c API hh.ru.
    :param hh_vac_params: Параметры для поиска вакансий hh.ru.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    # Делаем первый запрос для получения кол-ва найденных вакансий
    first_vacancy_request: dict = HH_api.get_vacancies_by_keyword(hh_vac_params())
    if first_vacancy_request.get('errors'):
        print(f'Ошибка {first_vacancy_request.get("errors")[0].get("type")}')
        return
    print(f'Найдено {first_vacancy_request["found"]} вакансий')
    if first_vacancy_request['found'] == 0:
        print('Вакансии не найдены')
        return
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 вакансия на страницу)
    for page in range(0, first_vacancy_request['found']):
        # Увеличиваем параметр страница на 1
        hh_vac_params.page = page
        # Получаем данные по вакансии
        vacancy: dict = HH_api.get_vacancies_by_keyword(hh_vac_params())
        vac_id: int = vacancy.get('items', [])[0].get('id')
        # Проверяем ЧС
        if DBManager.check_blacklisted_vacancies(vac_id=vac_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_vacancy_in_db(vac_id=vac_id):
            continue
        emp_id: int = vacancy.get('items', [])[0].get('employer').get('id')
        # Получаем данные по работодателю
        employer: dict = HH_api.get_employer_by_id(emp_id)
        vac_name: str = vacancy.get('items', [])[0].get('name')
        emp_name: str = vacancy.get('items', [])[0].get('employer').get('name')
        emp_industries: list = employer.get('industries', [])
        emp_industry: list = []
        for industry in emp_industries:
            emp_industry.append(industry.get('name'))
        emp_industry: str = ', '.join(emp_industry)
        emp_vac_count: int = employer.get('open_vacancies')
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
            vac_schedule: str or None = (vacancy.get('items', [])[0]
                                         .get('employment', None).get('name', None))
        except AttributeError:
            vac_schedule: str or None = None
        vac_requirement: str = (vacancy.get('items', [])[0]
                                .get('snippet').get('requirement', None))
        vac_responsibility: str = vacancy.get('items', [])[0].get('snippet').get('responsibility', None)
        vac_url: str = vacancy.get('items', [])[0].get('alternate_url')
        emp_url: str = vacancy.get('items', [])[0].get('employer').get('alternate_url')

        # Делаем вывод красивым
        if vac_pay_gross:
            vac_pay_gross_print: str = 'Да'
        else:
            vac_pay_gross_print: str = 'Нет'
        vac_pay_curr_print: str = 'Руб'

        print(
            f'---\033[1mВакансия №{page + 1} из {first_vacancy_request["found"]}\033[0m---\n'
            f'ID: {vac_id}. Название: {vac_name}. Заработная плата '
            f'от: {vac_pay_from}, до {vac_pay_to} {vac_pay_curr_print}. '
            f'До вычета налогов: {vac_pay_gross_print}\n'
            f'Компания: {emp_name}. Адрес: {vac_area}.\n'
            f'Обязанности: {vac_responsibility}.\n'
            f'Требования: {vac_requirement}.\n'
            f'Ссылка на вакансию: {vac_url}')

        # Выводим окно с выбором дальнейших действий
        user_choice: int = get_vacancies_navigation()
        # Сохранить в файл и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=emp_id, name=emp_name,
                                          industry=emp_industry,
                                          vac_count=emp_vac_count, url=emp_url)
            DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=emp_id, name=vac_name,
                                         area=vac_area, salary=vac_pay, currency=vac_pay_curr,
                                         gross=vac_pay_gross, schedule=vac_schedule,
                                         requirement=vac_requirement, responsibility=vac_responsibility,
                                         url=vac_url)
        # Добавить в ЧС
        elif user_choice == 2:
            DBManager.blacklist_vacancy(vac_id=vac_id)
        # Пропустить вакансию
        elif user_choice == 3:
            continue
        # Закончить работу с API hh.ru
        elif user_choice == 4:
            break


def get_employers_hh(HH_api, hh_emp_params) -> None:
    """
    Основная логика поиска компаний от hh.ru API.
    :param HH_api: Класс для API запросов.
    :param hh_emp_params: Параметры для API запроса.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    # Делаем первый запрос для получения кол-ва найденных компаний
    first_company_request: dict = HH_api.get_employers_by_keywords(hh_emp_params())
    if first_company_request.get('errors'):
        print(f'Ошибка {first_company_request.get("errors")[0].get("type")}')
        return
    if first_company_request['found'] == 0:
        print('Найдено 0 компаний')
        return
    print(f'Найдено {first_company_request["found"]} компаний')
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 компания на страницу)
    for page in range(0, first_company_request['found']):
        hh_emp_params.page = page
        emp: dict = HH_api.get_employers_by_keywords(hh_emp_params())
        emp_id: int = int(emp.get('items', [])[0].get('id'))
        # Проверяем ЧС
        if DBManager.check_blacklisted_employer(emp_id=emp_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_employer_in_db(emp_id=emp_id):
            continue
        employer: dict = HH_api.get_employer_by_id(emp_id)
        emp_industries: list = employer.get('industries', [])
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
        user_choice: int = get_employers_navigation()
        # Сохранить в дб и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=emp_id, name=emp_name, industry=emp_industry,
                                          vac_count=emp_vac_count, url=emp_url)
            save_user_choice = input('Сохранить все вакансии компании в файл?\n'
                                     '1 - Да\n2 - Нет (по умолчанию)\n')
            if save_user_choice == '1':
                if emp_vac_count == 0:
                    print('У компании нет активных вакансий')
                    continue
                for vacancy_num in range(emp_vac_count):
                    save_vacancy_by_id(vacancy_num=vacancy_num, emp_id=emp_id, HH_api=HH_api)
        # Добавить в ЧС
        elif user_choice == 2:
            DBManager.blacklist_employer(emp_id=emp_id)
        # Пропустить компанию
        elif user_choice == 3:
            continue
        # Закончить работу с API hh.ru
        elif user_choice == 4:
            return


def save_vacancy_by_id(vacancy_num: int, emp_id: int, HH_api) -> None:
    """
    :param vacancy_num: Порядковый номер вакансии для for loop
    :param emp_id: ID компании
    :param HH_api: Класс для API запросов
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    search_params: dict = {'page': vacancy_num,
                           'per_page': 1,
                           'employer_id': emp_id}
    vacancy = HH_api.get_vacancies_by_keyword(search_params)
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
