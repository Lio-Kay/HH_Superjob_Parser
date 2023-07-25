from db_func.db_manipulation_func import DBManager


def get_vacancies_superjob(SuperJobAPI, superjob_params):
    """
    Основная логика поиска вакансий от superjob.ru API
    :param SuperJobAPI: Класс для работы c API superjob.ru.
    :param superjob_params: Параметры для поиска вакансий superjob.ru.
    """
    vacancy: dict = SuperJobAPI.get_vacancies_by_keywords(superjob_params)
    if vacancy.get('error'):
        print(f'Ошибка {vacancy.get("error").get("message")}')
        return
    if vacancy.get('total') == 0:
        print('Вакансии не найдены')
        return
    vac_id: int = vacancy.get('objects', [])[0].get('id')
    # Проверяем на наличие вакансии в Ч
    if DBManager.check_blacklisted_vacancies(vac_id=vac_id):
        superjob_params.page += 1
        get_vacancies_superjob(SuperJobAPI, superjob_params)
    vac_name: str = vacancy.get('objects', [])[0].get('profession')
    vac_pay_from: int or str = vacancy.get('objects', [])[0].get('payment_from', 0)
    vac_pay_to: int or str = vacancy.get('objects', [])[0].get('payment_to', 0)
    vac_pay_curr: str = vacancy.get('objects', [])[0].get('currency')
    vac_employer: str = vacancy.get('objects', [])[0].get('firm_name')
    # Делаем вывод красивым
    if vac_pay_curr == 'RUR':
        vac_pay_curr: str = 'Руб'
    # Адрес не всегда указан полностью, ловим ошибки
    vac_area: dict or str = vacancy.get('objects', [])[0].get('address', 'Не указан')
    if vac_area is None:
        vac_area: str = 'Не указан'
    vac_responsibility: str = vacancy.get('objects', [])[0].get('work', 'Не указанны')
    if vac_responsibility is None:
        vac_responsibility = 'Не указанны'
    vac_requirement: str = vacancy.get('objects', [])[0].get('candidat', 'Не указанны')
    if vac_requirement is None:
        vac_requirement = 'Не указанны'
    vac_url: str = vacancy.get('objects', [])[0].get('link')
    if vac_pay_to and vac_pay_from:
        pay_to_be_saved: int = int((vac_pay_to + vac_pay_from) / 2)
    elif vac_pay_to == 0:
        pay_to_be_saved: int = vac_pay_from
    else:
        pay_to_be_saved = 0

    print(
        f'---\033[1mВакансия №{superjob_params.page+1}\033[0m---\n'
        f'ID: {vac_id}. Название: {vac_name}. Заработная плата '
        f'от: {vac_pay_from}, до {vac_pay_to} {vac_pay_curr}.\n'
        f'Компания: {vac_employer}. Адрес: {vac_area}.\n'
        f'Обязанности: {vac_requirement}.\n'
        f'Ссылка на вакансию: {vac_url}')

    # Выводим окно с выбором дальнейших действий
    user_choice: int = get_vacancies_navigation()
    # Сохранить в файл и добавить в ЧС
    if user_choice == 1:
        DBManager.save_vacancy_to_db(vac_id=vac_id, employer_id=emp_id, name=vac_name, area=vac_area,
                                     salary=vac_pay, currency=vac_pay_curr, gross=vac_pay_gross,
                                     schedule=vac_schedule,
                                     requirement=vac_requirement, responsibility=vac_responsibility,
                                     url=vac_url)
        superjob_params.page += 1
        get_vacancies_superjob(SuperJobAPI, superjob_params)
    # Добавить в ЧС
    elif user_choice == 2:
        DBManager.blacklist_vacancy(vac_id=vac_id)
        superjob_params.page += 1
        get_vacancies_superjob(SuperJobAPI, superjob_params)
    # Пропустить вакансию
    elif user_choice == 3:
        superjob_params.page += 1
        get_vacancies_superjob(SuperJobAPI, superjob_params)
    # Закончить работу с API superjob.ru
    elif user_choice == 4:
        return


def get_vacancies_navigation() -> int:
    """
    Функция для выбора действия с вакансией
    :return: Выбор в меню в числовом представлении.
    """
    user_choice: str = \
        input('\n1 - Сохранить вакансию в файл\n'
              '2 - Больше не показывать вакансию\n'
              '3 - Пропустить вакансию\n'
              '4 - Закончить работу с текущей платформой\n')
    while user_choice in ['1', '2', '3', '4']:
        if user_choice == '1':
            return 1
        elif user_choice == '2':
            return 2
        elif user_choice == '3':
            return 3
        elif user_choice == '4':
            return 4
        else:
            print('Неверный ввод')
            user_choice: str = \
                input('\n1 - Сохранить вакансию в файл\n'
                      '2 - Больше не показывать вакансию\n'
                      '3 - Пропустить вакансию\n'
                      f'4 - Закончить работу с текущей платформой\n')


def get_companies_navigation() -> int:
    """
    Функция для выбора действия с компаниями
    :return: Выбор в меню в числовом представлении
    """
    user_choice: str = \
        input('\n1 - Сохранить компанию в файл\n'
              '2 - Больше не показывать вакансию\n'
              '3 - Пропустить вакансию\n'
              '4 - Закончить работу с текущей платформой\n')
    while user_choice in ['1', '2', '3', '4']:
        if user_choice == '1':
            return 1
        elif user_choice == '2':
            return 2
        elif user_choice == '3':
            return 3
        elif user_choice == '4':
            return 4
        else:
            print('Неверный ввод')
            user_choice: str = \
                input('\n1 - Сохранить компанию в файл\n'
                      '2 - Больше не показывать вакансию\n'
                      '3 - Пропустить вакансию\n'
                      f'4 - Закончить работу с текущей платформой\n')
