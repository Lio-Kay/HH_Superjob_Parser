from api.api_requests import HeadHunterAPI, SuperJobAPI
from search_params.hh_search_params import HHVacSearchParams, HHEmpSearchParams
from search_params.superjob_search_params import SuperjobVacSearchParams, SuperjobEmpSearchParams
from search_func.set_search_params import select_platforms, get_vacancies, get_employers
from db_func.db_manipulation_func import DBCreator


MENU: str = """
'1': Искать новые вакансии
'2': Искать новые компании
'3': Работать с текущими данными
'0': Выйти из программы
"""
MENU_SEARCH_VAC: str = """
'1': Установить платформы для поиска
'2': Установить параметры поиска на hh.ru
'3': Установить параметры поиска на superjob.ru
'9': Вывести вакансии
'0': Назад
"""
MENU_SEARCH_EMP: str = """
'1': Установить платформы для поиска
'2': Установить параметры поиска на hh.ru
'3': Установить параметры поиска на superjob.ru
'9': Вывести работодателей
'0': Назад
"""
SEARCH_PLATFORMS: str = """
'1': headhunter.ru
'2': superjob.ru
'9': Все
'0': Назад
"""
MENU_WORK_WITH_DATA: str = """
'1': Получить общую информацию о файле
'2': Вывести все вакансии
'3': Сравнить вакансии по ЗП
'4': Удалить вакансию из файла
'5': Отчистить файл
'0': Назад
"""


def user_interface() -> None:
    """
    Основной пользовательский интерфейс.
    Запускается через 'if __name__ == '__main__'.
    """

    # Проверяем соединение
    HeadHunterAPI.test_connection()
    SuperJobAPI.test_connection()

    # Создаем БД
    DBCreator.create_database()
    DBCreator.create_tables()

    # Экземпляры классов с параметрами поиска
    hh_vac_params = HHVacSearchParams()
    superjob_vac_params = SuperjobVacSearchParams()
    hh_emp_params = HHEmpSearchParams()
    superjob_emp_params = SuperjobEmpSearchParams()

    # Поисковые платформы
    current_vac_search_platforms = 'headhunter.ru, superjob.ru'
    current_emp_search_platforms = 'headhunter.ru, superjob.ru'

    menu_input = input(MENU)
    while menu_input != '0':
        # Искать новые вакансии
        if menu_input == '1':
            menu_vac_search_input = input(MENU_SEARCH_VAC)
            match menu_vac_search_input:
                # Назад
                case '0':
                    menu_input = input(MENU)
                # Установить платформу для поиска
                case '1':
                    current_vac_search_platforms = (
                        select_platforms(current_vac_search_platforms, SEARCH_PLATFORMS))
                # Установить ключевые данные для hh.ru
                case '2':
                    hh_vac_params.hh_set_params_for_a_search()
                # Установить ключевые данные для superjob.ru
                case '3':
                    superjob_vac_params.superjob_set_params_for_a_search()
                # Вывести вакансии
                case '9':
                    get_vacancies(current_vac_search_platforms, HeadHunterAPI, hh_vac_params,
                                  SuperJobAPI, superjob_vac_params)
        # Искать новые компании
        elif menu_input == '2':
            menu_emp_search_input = input(MENU_SEARCH_EMP)
            match menu_emp_search_input:
                # Назад
                case '0':
                    menu_input = input(MENU)
                # Установить платформу для поиска
                case '1':
                    current_emp_search_platforms = select_platforms(current_emp_search_platforms,
                                                                    SEARCH_PLATFORMS)
                # Установить ключевые данные для hh.ru
                case '2':
                    hh_emp_params.hh_set_params_for_a_search()
                # Установить ключевые данные для superjob.ru
                case '3':
                    superjob_emp_params.superjob_set_params_for_a_search()
                # Вывести вакансии
                case '9':
                    get_employers(current_emp_search_platforms, HeadHunterAPI, hh_emp_params,
                                  SuperJobAPI, superjob_emp_params)
        # Получить данные из файла
        elif menu_input == '3':
            user_menu_get_input: str = input(MENU_WORK_WITH_DATA)
            match user_menu_get_input:
                # Назад
                case '0':
                    menu_input: str = input(MENU)

    print('Программа завершена')


if __name__ == '__main__':
    user_interface()
