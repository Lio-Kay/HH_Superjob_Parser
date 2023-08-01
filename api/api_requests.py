"""
Этот модуль содержит классы для API запросов к hh.ru и superjob.ru
"""

from abc import ABC, abstractmethod
from inspect import currentframe
import logging as log
import os
import pathlib as pl

import requests

log.basicConfig(level=log.DEBUG,
                filename=pl.Path.cwd() / 'project_logs.log', filemode='w')


class AbstractAPI(ABC):
    """
    Абстрактный класс для создания API различных платформ
    """

    @classmethod
    @abstractmethod
    def test_connection(cls):
        """Проверка соединения"""

    @classmethod
    @abstractmethod
    def get_vacancies(cls, params) -> dict:
        """
        Поиск по вакансиям
        :param params: Данные из экземпляра класса hh_params в user_interface() main.py
        :return: Список вакансий на основании запроса
        """

    @classmethod
    @abstractmethod
    def get_employers_by_keywords(cls, params) -> dict:
        """
        Поиск по работодателям
        :param params: Данные из экземпляра класса hh_params в user_interface() main.py
        :return: Список компаний на основании запроса
        """

    @classmethod
    @abstractmethod
    def get_employer_by_id(cls, emp_id) -> dict:
        """
        Поиск работодателя по id
        :param emp_id: id работодателя
        :return: Данные по работодателю
        """

    @classmethod
    @abstractmethod
    def get_regions(cls, params) -> dict:
        """
        Получение списка регионов на основе ввода
        :param params: Ввод пользователя для получения списка регионов
        :return: Список регионов с наименованием региона и id
        """


class HeadHunterAPI(AbstractAPI):
    """
    Класс для работы с API HH.ru
    """

    vacancies_api: str = 'https://api.hh.ru/vacancies/'
    employers_api: str = 'https://api.hh.ru/employers/'
    regions_api: str = 'https://api.hh.ru/suggests/areas/'

    @classmethod
    def test_connection(cls) -> None:
        """Проверка соединения"""
        if requests.get(cls.employers_api, timeout=10).status_code == 200:
            print(f'Подключение к {cls.__name__} успешно')
        else:
            # TODO Проверить функциональность
            # Пытаемся пройти captcha
            print(requests.get(cls.employers_api, timeout=10).status_code)
            error_link: str = requests.get(url=cls.employers_api, timeout=10) \
                .json().get('errors')[0].get('captcha_url')
            cls.employers_api: str = error_link + '&backurl=' + 'http://127.0.0.1:5500/index.html'
            print(cls.employers_api)
            if requests.get(cls.employers_api, timeout=10).status_code == 200:
                print(f'Подключение к {cls.__name__} успешно')

    @classmethod
    def get_vacancies(cls, params: dict) -> dict:
        """
        Поиск по вакансиям
        :param params: Данные из экземпляра класса hh_params в user_interface() main.py
        :return: Список вакансий на основании запроса
        """
        data: dict = requests.get(url=cls.vacancies_api, params=params, timeout=10).json()

        return data

    @classmethod
    def get_employers_by_keywords(cls, params: dict) -> dict:
        """
        Поиск по работодателям
        :param params: Данные из экземпляра класса hh_params в user_interface() main.py
        :return: Список компаний на основании запроса
        """
        data: dict = requests.get(url=cls.employers_api, params=params, timeout=10).json()

        return data

    @classmethod
    def get_employer_by_id(cls, emp_id: str) -> dict:
        """
        Поиск работодателя по id
        :param emp_id: id работодателя
        :return: Данные по работодателю
        """
        emp_id: str = str(emp_id)
        data: dict = requests.get(cls.employers_api + emp_id, timeout=10).json()

        return data

    @classmethod
    def get_regions(cls, params: dict) -> dict:
        """
        Получение списка регионов на основе ввода
        :param params: Ввод пользователя для получения списка регионов
        :return: Список регионов с наименованием региона и id
        """
        data: dict = requests.get(url=cls.regions_api, params=params, timeout=10).json()

        return data


class SuperJobAPI(AbstractAPI):
    """
    Класс для работы с API superjob.ru
    """

    # Токен superjob API
    api_key: str = os.getenv('SUPERJOB_API')
    headers: str = {'X-Api-App-Id': api_key}

    vacancies_api: str = 'https://api.superjob.ru/2.0/vacancies/'
    employers_api: str = 'https://api.superjob.ru/2.0/clients/'
    regions_api: str = 'https://api.superjob.ru/2.0/towns/'

    @classmethod
    def test_connection(cls) -> None:
        """Проверка соединения"""
        if requests.get(cls.vacancies_api, headers=cls.headers, timeout=10).status_code == 200:
            print(f'Подключение к {cls.__name__} успешно')
        else:
            print(requests.get(cls.vacancies_api, headers=cls.headers, timeout=10).status_code)

    @classmethod
    def get_vacancies(cls, params) -> dict:
        """
        Поиск по вакансиям
        :param params: Данные из экземпляра класса superjob_params в user_interface() main.py
        :return: Список вакансий на основании запроса
        """
        cls.vacancies_api: str = 'https://api.superjob.ru/2.0/vacancies/'
        cls.vacancies_api: str = cls.vacancies_api + f'?keyword={params.update_keyword}&' \
                                                     f'order_field={params.update_search_order[0]}&' \
                                                     f'payment_from={params.update_salary}&' \
                                                     f'no_agreement={params.update_only_w_salary[0]}&' \
                                                     f't={params.update_region_and_region_id[0]}&' \
                                                     f'type_of_work={params.update_employment_and_emp_rus[0]}&' \
                                                     f'count={1}&' \
                                                     f'page={params.page}'

        data: dict = requests.get(url=cls.vacancies_api, headers=cls.headers, timeout=10).json()

        return data

    @classmethod
    def get_employers_by_keywords(cls, params) -> dict:
        """
        Поиск по работодателям
        :param params: Данные из экземпляра класса superjob_params в user_interface() main.py
        :return: Список компаний на основании запроса
        """
        cls.employers_api: str = 'https://api.superjob.ru/2.0/vacancies/'
        cls.employers_api: str = cls.employers_api + f'?keyword={params.update_search_txt}&' \
                                                     f't={params.update_region_and_region_id[0]}&' \
                                                     f'all={params.update_show_without_vac}&' \
                                                     f'count={1}&' \
                                                     f'page={params.page}'

        data: dict = requests.get(url=cls.employers_api, headers=cls.headers, timeout=10).json()

        return data

    @classmethod
    def get_employer_by_id(cls, emp_id: str) -> dict:
        """
        Поиск работодателя по id
        :param emp_id: id работодателя
        :return: Данные по работодателю
        """
        emp_id: str = str(emp_id)
        data: dict = requests.get(cls.employers_api + emp_id, headers=cls.headers, timeout=10).json()

        return data

    @classmethod
    def get_regions(cls, params: str) -> dict:
        """
        Получение списка регионов на основе ввода
        :param params: Ввод пользователя для получения списка регионов
        :return: Список регионов с наименованием и id
        """
        cls.regions_api: str = 'https://api.superjob.ru/2.0/towns/'
        cls.regions_api = cls.regions_api + f'?keyword={params}&all=0&genitive=1'
        data = requests.get(url=cls.regions_api, headers=cls.headers, timeout=10)

        return data.json()
