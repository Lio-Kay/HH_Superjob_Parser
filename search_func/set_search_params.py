"""
Файл для выбора поисковых платформ и
точка запуска get_vacancies разных платформ.
"""

from inspect import currentframe
import logging as log
import pathlib as pl

from search_func.hh_search_func import get_vacancies_hh, get_employers_hh
from search_func.superjob_search_func import get_vacancies_superjob, get_employers_superjob

log.basicConfig(level=log.DEBUG,
                filename=pl.Path.cwd() / 'project_logs.log', filemode='w')


def select_platforms(current_search_platforms: str, search_platforms: str) -> str:
    """
    Функция блока user_interface() для выбора списка платформ для API запросов.
    :argument current_search_platforms: Строка search_params содержащая все данные для поиска.
    :argument search_platforms: Меню доступных платформ для поиска.
    :return: Обновленная строка current_search_platforms.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    print(f'Выбранные платформы: {current_search_platforms}')
    user_menu_search_platforms_input: str = input(search_platforms)
    match user_menu_search_platforms_input:
        case '0':
            return current_search_platforms
        case '1':
            new_search_platforms: str = 'headhunter.ru'
        case '2':
            new_search_platforms: str = 'superjob.ru'
        case '9':
            new_search_platforms: str = 'headhunter.ru, superjob.ru'

    return new_search_platforms


def get_vacancies(search_platforms: str, HH_api, hh_vac_params,
                  Superjob_api, superjob_vac_params) -> None:
    """
    Функция блока user_interface() для начала запросов к выбранным API.
    :param search_platforms: Строка с выбранными платформами для поиска.
    :param HH_api: Класс для работы c API hh.ru.
    :param hh_vac_params: Параметры для поиска вакансий hh.ru.
    :param Superjob_api: Класс для работы c API superjob.ru.
    :param superjob_vac_params: Параметры для поиска вакансий superjob.ru.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    if search_platforms == 'headhunter.ru':
        get_vacancies_hh(HH_api, hh_vac_params)
    elif search_platforms == 'superjob.ru':
        get_vacancies_superjob(Superjob_api, superjob_vac_params)
    elif search_platforms == 'headhunter.ru, superjob.ru':
        get_vacancies_hh(HH_api, hh_vac_params)
        get_vacancies_superjob(Superjob_api, superjob_vac_params)


def get_employers(search_platforms: str, HH_api, hh_params, Superjob_api, superjob_params) -> None:
    """
    Функция блока user_interface() для начала запросов к выбранным API.
    :param search_platforms: Строка с выбранными платформами для поиска.
    :param hh_params: Параметры для поиска работодателей hh.ru.
    :param HH_api: Класс для работы c API hh.ru.
    :param Superjob_api: Класс для работы c API superjob.ru.
    :param superjob_params: Параметры для поиска работодателей superjob.ru.
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    if search_platforms == 'headhunter.ru':
        get_employers_hh(HH_api, hh_params)
    elif search_platforms == 'superjob.ru':
        get_employers_superjob(Superjob_api, superjob_params)
    elif search_platforms == 'headhunter.ru, superjob.ru':
        get_employers_hh(HH_api, hh_params)
        get_employers_superjob(Superjob_api, superjob_params)
