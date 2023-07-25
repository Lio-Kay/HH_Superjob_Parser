from db_func.db_manipulation_func import DBManager
from search_func.search_navigation import get_vacancies_navigation, get_companies_navigation
from forex_python.converter import CurrencyRates
import logging
from inspect import currentframe
import pathlib


logging.basicConfig(level=logging.DEBUG, filename=pathlib.Path.cwd() / 'project_logs.log', filemode='w')


converter = CurrencyRates()


def get_vacancies_hh(HH_API, hh_params) -> None:
    """
    Основная логика поиска вакансий от hh.ru API
    :param HH_API: Класс для работы c API hh.ru.
    :param hh_params: Параметры для поиска вакансий hh.ru.
    """
    # Делаем первый запрос для получения кол-ва найденных вакансий
    first_vacancy_request: dict = HH_API.get_vacancies_by_keywords(hh_params())
    if first_vacancy_request.get('errors'):
        print(f'Ошибка {first_vacancy_request.get("errors")[0].get("type")}')
        return
    print(f'Найдено {first_vacancy_request["found"]} вакансий')
    if first_vacancy_request['found'] == 0:
        print('Найдено 0 вакансий')
        return
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 вакансия на страницу)
    for page in range(0, first_vacancy_request['found']):
        # Увеличиваем параметр страница на 1
        hh_params.page = page
        # Получаем данные по вакансии
        vacancy: dict = HH_API.get_vacancies_by_keywords(hh_params())
        vac_id: int = vacancy.get('items', [])[0].get('id')
        # Проверяем ЧС
        if DBManager.check_blacklisted_vacancies(vac_id=vac_id):
            continue
        # Проверяем существующие вакансии
        if DBManager.check_vacancy_in_db(vac_id=vac_id):
            continue
        emp_id: int = vacancy.get('items', [])[0].get('employer').get('id')
        # Получаем данные по работодателю
        employer: dict = HH_API.get_employer_by_id(emp_id)
        vac_name: str = vacancy.get('items', [])[0].get('name')
        emp_name: str = vacancy.get('items', [])[0].get('employer').get('name')
        emp_industries: str = employer.get('industries', [])
        emp_industry: list = []
        for industry in emp_industries:
            emp_industry.append(industry.get('name'))
        emp_industry: str = ' ,'.join(emp_industry)
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
            vac_schedule: str or None = vacancy.get('items', [])[0].get('employment', None).get('name', None)
        except AttributeError:
            vac_schedule: str or None = None
        vac_requirement: str = vacancy.get('items', [])[0].get('snippet').get('requirement', None)
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
            f'от: {vac_pay_from}, до {vac_pay_to} {vac_pay_curr_print}. До вычета налогов: {vac_pay_gross_print}\n'
            f'Компания: {emp_name}. Адрес: {vac_area}.\n'
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
        # Закончить работу с API hh.ru
        elif user_choice == 4:
            break


def get_new_companies_hh(HH_API, hh_params) -> None:
    """
    :param HH_API: Класс для API запросов
    :param hh_params: Параметры для API запроса
    """
    # Делаем первый запрос для получения кол-ва найденных компаний
    first_company_request: dict = HH_API.get_employers_by_keywords(hh_params())
    if first_company_request.get('errors'):
        print(f'Ошибка {first_company_request.get("errors")[0].get("type")}')
        return
    if first_company_request['found'] == 0:
        print('Найдено 0 компаний')
        return
    print(f'Найдено {first_company_request["found"]} компаний')
    # Создаем цикл на основе кол-ва найденных страниц (при условии - 1 компания на страницу)
    for page in range(0, first_company_request['found']):
        company: dict = HH_API.get_employers_by_keywords(hh_params())
        company_id: int = int(company.get('items', [])[0].get('id'))
        # Проверяем на наличие работодателя в ДБ
        if DBManager.check_blacklisted_employer(emp_id=company_id):
            hh_params.page += 1
            continue
        company_name: str = company.get('items', [])[0].get('name')
        company_vacancies_count: int = company.get('items', [])[0].get('open_vacancies')
        company_url: str = company.get('items', [])[0].get('alternate_url')

        print(
            f'---\033[1mКомпания №{page + 1} из {first_company_request["found"]}\033[0m---\n'
            f'ID: {company_id}. Название: {company_name}.'
            f'Кол-во вакансий компании: {company_vacancies_count}. Ссылка на компанию: {company_url}')

        # Выводим окно с выбором дальнейших действий
        user_choice: int = get_companies_navigation()
        # Сохранить в дб и добавить в ЧС
        if user_choice == 1:
            DBManager.save_employer_to_db(comp_id=company_id, name=company_name, vac_count=company_vacancies_count)
            if company_vacancies_count == 0:
                print('У компании нет активных вакансий')
                continue
            for vacancy_num in range(company_vacancies_count):
                save_all_vacancies(vacancy_num=vacancy_num, company_id=company_id, api=api)
            search_params.page += 1
        # Добавить в ЧС
        elif user_choice == 2:
            DBManager.save_employer_to_db(comp_id=company_id, name=company_name, vac_count=company_vacancies_count,
                                          blacklisted=True, db_config=db_config)
            search_params.page += 1
        # Пропустить компанию
        elif user_choice == 3:
            continue
        # Закончить работу с API hh.ru
        elif user_choice == 4:
            return


def save_all_vacancies(vacancy_num: int, company_id: int, api) -> None:
    """
    :param vacancy_num: Порядковый номер вакансии для for loop
    :param company_id: ID компании
    :param api: Экземпляр класса для API запросов
    """
    search_params: dict = {'page': vacancy_num,
                           'per_page': 1,
                           'employer_id': company_id}
    vacancy = api.get_vacancies_hh(search_params)
    vac_id: int = int(vacancy.get('items', [])[0].get('id'))
    vac_name: str = vacancy.get('items', [])[0].get('name')
    # Адрес не всегда указан полностью, ловим ошибки
    try:
        vac_employer_raw_loc: dict = vacancy.get("items", [])[0].get("address")
        vac_area: str = f'{vac_employer_raw_loc.get("city")} {vac_employer_raw_loc.get("street")}' \
                        f'{vac_employer_raw_loc.get("building")}'
        if vac_area == 'None NoneNone':
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
        vac_pay: None = None
    try:
        vac_pay_curr: str or None = vacancy.get('items', [])[0].get('salary').get('currency')
    except AttributeError:
        vac_pay_curr: str = 'RUB'
    # Переводим зп в рубли
    if vac_pay_curr == 'USD' and vac_pay is not None:
        vac_pay = converter.convert('USD', 'RUB', vac_pay)
        vac_pay_curr = 'RUB'
    elif vac_pay_curr == 'EUR' and vac_pay is not None:
        vac_pay = converter.convert('EUR', 'RUB', vac_pay)
        vac_pay_curr = 'RUB'
    elif vac_pay_curr == 'KZT' and vac_pay is not None:
        vac_pay = converter.convert('KZT', 'RUB', vac_pay)
        vac_pay_curr = 'RUB'
    else:
        vac_pay_curr = 'RUB'
    try:
        vac_pay_gross: bool or None = vacancy.get('items', [])[0].get('salary').get('gross')
    except AttributeError:
        vac_pay_gross: bool or None = None
    try:
        vac_schedule: str or None = vacancy.get('items', [])[0].get('employment', None).get('name', None)
    except AttributeError:
        vac_schedule: str or None = None
    vac_requirement: str = vacancy.get('items', [])[0].get('snippet').get('requirement', None)
    vac_responsibility: str = vacancy.get('items', [])[0].get('snippet').get('responsibility', None)
    vac_url: str = vacancy.get('items', [])[0].get('alternate_url')

    DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=company_id, name=vac_name, area=vac_area,
                                 salary=vac_pay, currency=vac_pay_curr, gross=vac_pay_gross, schedule=vac_schedule,
                                 requirement=vac_requirement, responsibility=vac_responsibility, url=vac_url)
