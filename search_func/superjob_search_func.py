"""
Этот файл содержит в себе функции для получения данных от superjob.ru,
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


def get_vacancies_superjob(SuperJobAPI, superjob_vac_params):
    """
    Основная логика поиска вакансий от superjob.ru API.
    :param SuperJobAPI: Класс для работы c API superjob.ru.
    :param superjob_vac_params: Параметры для поиска вакансий superjob.ru.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    first_vacancy_request: dict = SuperJobAPI.get_vacancies_by_keyword(superjob_vac_params)
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
        vacancy: dict = SuperJobAPI.get_vacancies_by_keyword(superjob_vac_params)
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
            vac_schedule: str or None = (
                vacancy.get('objects', [])[0].get('type_of_work').get('title'))
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
        # Закончить работу с API superjob.ru
        elif user_choice == 4:
            return


def get_employers_superjob(SuperJobAPI, superjob_params):
    """
    Основная логика поиска компаний от superjob.ru API.
    :param SuperJobAPI: Класс для работы c API superjob.ru.
    :param superjob_params: Параметры для поиска вакансий superjob.ru.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    # Делаем первый запрос для получения кол-ва найденных компаний
    first_company_request: dict = SuperJobAPI.get_employers_by_keywords(superjob_params)
    if first_company_request.get('errors'):
        print(f'Ошибка {first_company_request.get("errors")[0].get("type")}')
        return
    if first_company_request['total'] == 0:
        print('Найдено 0 компаний')
        return
    print(f'Найдено {first_company_request["total"]} компаний')
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 компания на страницу)
    for page in range(0, first_company_request['total']):
        superjob_params.page = page
        emp: dict = SuperJobAPI.get_employers_by_keywords(superjob_params)
        emp_id: int = int(emp.get('objects', [])[0].get('id'))
        # Проверяем ЧС
        if DBManager.check_blacklisted_employer(emp_id=emp_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_employer_in_db(emp_id=emp_id):
            continue
        print(emp)
        emp_industries: str = emp.get('objects', [])[0].get('industry', [])
        emp_industry: list = []
        for industry in emp_industries:
            emp_industry.append(industry.get('title'))
        emp_industry: str = ' ,'.join(emp_industry)
        emp_name: str = emp.get('objects', [])[0].get('title')
        emp_vac_count: int = emp.get('objects', [])[0].get('vacancy_count')
        emp_url: str = emp.get('objects', [])[0].get('link')

        print(
            f'---\033[1mКомпания №{page + 1} из {first_company_request["total"]}\033[0m---\n'
            f'ID: {emp_id}. Название: {emp_name}.'
            f'Сфера деятельности: {emp_industry}.'
            f'Кол-во вакансий компании: {emp_vac_count}. Ссылка на компанию: {emp_url}')

        # Выводим окно с выбором дальнейших действий
        user_choice: int = get_vacancies_navigation()
        print(emp)
        # Сохранить в файл и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=emp_id, name=emp_name, industry=emp_industry,
                                          vac_count=emp_vac_count, url=emp_url)
            save_user_choice = input('Сохранить все вакансии компании в файл?\n'
                                     '1 - Да\n2 - Нет (по умолчанию)\n')
            if save_user_choice == '1':
                if emp_vac_count == 0:
                    print('У компании нет активных вакансий')
                else:
                    for vacancy_num in range(emp_vac_count):
                        save_vacancy_by_id(vacancy_num=vacancy_num,
                                           emp_id=emp_id, SuperjobAPI=SuperJobAPI)
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
    :param vacancy_num: Порядковый номер вакансии для for loop.
    :param emp_id: ID компании.
    :param SuperjobAPI: Класс для API запросов.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    search_params: dict = {'page': vacancy_num,
                           'id_client': emp_id}
    vacancy = SuperjobAPI.get_vacancies_by_id(search_params)
    vac_id: int = vacancy.get('objects', [])[0].get('id')
    # Проверяем на наличие вакансии в ЧС
    if DBManager.check_blacklisted_vacancies(vac_id=vac_id):
        return
    # Проверяем существующие вакансии
    if DBManager.check_vacancy_in_db(vac_id=vac_id):
        return
    emp_id: int = vacancy.get('objects', [])[0].get('id_client')
    employer: dict = SuperjobAPI.get_employer_by_id(emp_id)
    vac_name: str = vacancy.get('objects', [])[0].get('profession')
    emp_name: str = employer.get('title')
    emp_industries: str = employer.get('industry', [])
    emp_industry: list = []
    for industry in emp_industries:
        emp_industry.append(industry.get('title'))
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
    # Делаем вывод красивым
    if vac_pay_curr == 'RUR':
        vac_pay_curr: str = 'Руб'
    vac_pay_gross = False

    DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=emp_id, name=vac_name, area=vac_area,
                                 salary=vac_pay, currency=vac_pay_curr, gross=vac_pay_gross,
                                 schedule=vac_schedule,
                                 requirement=vac_requirement, responsibility=vac_responsibility,
                                 url=vac_url)
