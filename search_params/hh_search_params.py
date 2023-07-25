from api.api_requests import HeadHunterAPI

import re


class HHVacSearchParams:
    """
    Класс выбора ключевых параметров для запросов вакансий hh.ru
    """

    # Текущая страница поиска
    page = 0

    def __init__(self, keywords: list = ['python'], keywords_rus: str = 'python', region: str = 'Москва',
                 region_id: int = 1, employment: set = set({'full'}), employment_rus: set = set({'Полная'}),
                 salary: int = 80_000, only_w_salary: bool = False, only_w_salary_rus: str = 'Да',
                 search_order: str = 'publication_time', search_order_rus: str = 'По дате публикации'):
        """
        :param keywords: Ключевые слова на языке запросов.
        :param keywords_rus: Ключевые слова в читабельном виде.
        :param region: Название региона.
        :param region_id: ID региона.
        :param employment: Типы занятости.
        :param employment_rus: Типы занятости в читабельном виде.
        :param salary: ЗП.
        :param only_w_salary: Параметр только с указанием зп.
        :param only_w_salary_rus: Параметр только с указанием зп в читабельном виде.
        :param search_order: Способ сортировки.
        :param search_order_rus: Способ сортировки в читабельном виде.
        """

        self.__keywords: list = keywords
        self.__keywords_rus: str = keywords_rus
        self.__region: str = region
        self.__region_id: int = region_id
        self.__employment: set = employment
        self.__employment_rus: set = employment_rus
        self.__salary: int = salary
        self.__only_w_salary: bool = only_w_salary
        self.__only_w_salary_rus: salary = only_w_salary_rus
        self.__search_order: str = search_order
        self.__search_order_rus: str = search_order_rus

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__keywords},{self.__region},{self.__region_id}, {self.__employment},' \
               f'{self.__employment_rus},{self.__salary},{self.__only_w_salary},{self.__only_w_salary_rus},' \
               f'{self.__search_order}, {self.__search_order_rus})'

    def __str__(self):
        return f'Параметры поиска. Ключевые слова: {self.__keywords}, Область поиска: {self.__region},' \
               f'Типы занятости: {self.__employment}, Ожидаемая зп {self.__salary},' \
               f'Только с указанием зп: {self.__only_w_salary_rus}, Сортировка по: {self.__search_order_rus}'

    def __call__(self, *args, **kwargs) -> dict:
        """
        :return: Словарь для API запроса
        """
        return {'page': self.page,
                'per_page': 1,
                'text': self.update_keywords[0],
                'employment': self.update_employment_and_emp_rus[0],
                'area': self.update_region_and_region_id[0],
                'salary': self.update_salary,
                'only_with_salary': self.update_only_w_salary[0],
                'vacancy_search_order': self.update_search_order[0]}

    @property
    def update_keywords(self) -> tuple[list, str]:
        return self.__keywords, self.__keywords_rus

    @update_keywords.setter
    def update_keywords(self, new_keywords: str) -> None:
        new_keywords: str or list = new_keywords.casefold().strip().split(',')
        if new_keywords == ['']:
            self.update_keywords_loop(new_keywords)
        # Валидация введенных данных
        new_keywords: list = [entry.strip() for entry in new_keywords]
        new_keywords: list = [keyword for keyword in new_keywords if keyword != '']
        if len(new_keywords) == 1:
            self.__keywords: str = new_keywords[0]
            self.__keywords_rus: str = new_keywords[0]
        elif len(new_keywords) > 1:
            selected_text_query_language: list = [entry + ' AND ' + new_keywords[-1] for entry in new_keywords[0:-1]]
            self.__keywords: str = ''.join(selected_text_query_language)
            self.__keywords_rus: str = ', '.join(new_keywords)

    @staticmethod
    def update_keywords_loop(new_keywords) -> str or list:
        """
        Цикл для update_keywords()
        :return: Tuple со списком регионов и их кол-вом
        """
        while new_keywords == ['']:
            print('Введите корректные данные')
            new_keywords: str or list = \
                input('Введите ключевые слова через запятую\n').casefold().strip().split(',')
        return new_keywords

    @property
    def update_region_and_region_id(self) -> tuple:
        return self.__region_id, self.__region

    @update_region_and_region_id.setter
    def update_region_and_region_id(self, new_region: str) -> None:
        new_region: str = new_region.casefold()
        results: dict = self.update_region_loop(new_region)
        # Если ничего не нашли - повторяем поиск
        if results is False:
            new_region: str = \
                input('Введите область/город для поиска.\n'
                      '\033[1m' + 'Искомый текст должен быть на русском и длиннее 2 букв\n' + '\033[0m').casefold()
            results = self.update_region_loop(new_region)
        print(f'Найдено {results[1]} результатов:')
        # Выводим результаты
        for idx, city in enumerate(results[0], start=1):
            print(f'{idx}. {city["text"]}')
            results[0][idx - 1].update({'Index': f'{idx}'})
        user_specified_region: str = input('Уточните область/город по номеру:\n')
        # Проверяем, что пользователь ввел значение для выбора области поиска из списка
        while not any(d['Index'] == user_specified_region for d in results[0]):
            print('Региона с таким номером нет в списке')
            user_specified_region: str = input('Уточните область/город по номеру:\n')
        # Обновляем ID для поиска
        self.__region_id: int = \
            list((entry['id'] for entry in results[0]
                  if entry['Index'] == user_specified_region))[0]
        # Обновляем текстовое обозначение области поиска
        self.__region = \
            list((entry['text'] for entry in results[0]
                  if entry['Index'] == user_specified_region))[0]

    @staticmethod
    def update_region_loop(new_region) -> tuple[dict, int] or bool:
        """
        Цикл для update_region_and_region_id()
        :return: Tuple со списком регионов и их кол-вом
        """
        while len(new_region) < 2 \
                or not all([data.isalpha() for data in new_region]) \
                or not bool(re.search('[а-яА-Я]', new_region)):
            print('Введите корректные данные')
            new_region: str = \
                input('Введите область/город для поиска.\n'
                      '\033[1m' + 'Искомый текст должен быть на русском и длиннее 2 букв\n' + '\033[0m').casefold()
        string: dict = {'text': new_region}
        number_of_found_regions: int = len(HeadHunterAPI.get_regions(params=string)['items'])
        if number_of_found_regions == 0:
            print(f'\nНайдено 0 результатов')
            return False
        correct_region: dict = HeadHunterAPI.get_regions(params=string)['items']
        return correct_region, number_of_found_regions

    @property
    def update_employment_and_emp_rus(self) -> tuple[set, set]:
        return self.__employment, self.__employment_rus

    @update_employment_and_emp_rus.setter
    def update_employment_and_emp_rus(self, new_employment: str) -> None:
        results: bool = self.update_employment_loop(new_employment)
        while results:
            print(f'\nТекущая занятость: {", ".join(self.update_employment_and_emp_rus[1])}')
            new_employment: str = input('Выберите типы занятости:\n'
                                        '1 - Полная\n'
                                        '2 - Частичная\n'
                                        '3 - Проектная\n'
                                        '4 - Стажировка\n'
                                        '5 - Отчистить список\n'
                                        'Enter - Закончить выбор\n')
            results: bool = self.update_employment_loop(new_employment)
        if len(self.__employment) == 0:
            self.__employment_rus: set = set({'Полная', 'Частичная', 'Проектная', 'Стажировка'})
            self.__employment: set = set({'full', 'part', 'project', 'probation'})

    def update_employment_loop(self, new_employment: str) -> bool:
        """
        Цикл для update_employment_and_emp_rus()
        :return: False если ввод не поступил
        """
        if new_employment == '1':
            self.__employment_rus.add('Полная')
            self.__employment.add('full')
            return True
        elif new_employment == '2':
            self.__employment_rus.add('Частичная')
            self.__employment.add('part')
            return True
        elif new_employment == '3':
            self.__employment_rus.add('Проектная')
            self.__employment.add('project')
            return True
        elif new_employment == '4':
            self.__employment_rus.add('Стажировка')
            self.__employment.add('probation')
            return True
        elif new_employment == '5':
            self.__employment_rus.clear()
            self.__employment.clear()
            return True
        elif new_employment == '':
            return False

    @property
    def update_salary(self) -> int:
        return self.__salary

    @update_salary.setter
    def update_salary(self, new_salary: str) -> None:
        try:
            user_selected_salary: int = int(new_salary)
        except ValueError:
            print('Некорректный ввод. Зп установленна на 50 тыс. рублей')
            self.__salary: int = 50_000
            return
        if user_selected_salary == '0':
            self.__salary: int = 50_000
        else:
            self.__salary = user_selected_salary

    @property
    def update_only_w_salary(self) -> tuple[bool, str]:
        return self.__only_w_salary, self.__only_w_salary_rus

    @update_only_w_salary.setter
    def update_only_w_salary(self, new_only_w_salary: str) -> None:
        if new_only_w_salary != '2':
            self.__only_w_salary_rus = 'Нет'
            self.__only_w_salary = False
        elif new_only_w_salary == '2':
            self.__only_w_salary_rus = 'Да'
            self.__only_w_salary = True

    @property
    def update_search_order(self) -> tuple[str, str]:
        return self.__search_order, self.__search_order_rus

    @update_search_order.setter
    def update_search_order(self, new_search_order: str) -> None:
        if new_search_order != '2':
            self.__search_order_rus = 'По дате публикации'
            self.__search_order = 'publication_time'
        elif new_search_order == '2':
            self.__search_order_rus = 'По убыванию дохода'
            self.__search_order = 'salary_desc'

    def hh_set_params_for_a_search(self) -> None:
        """
        Основная логика выбора параметров для поиска
        :return: экземпляр класса hh_search_params
        """
        # Выбор ключевых слов для поиска
        self.update_keywords = \
            input('Введите ключевые слова через запятую\n')
        # Выбор региона
        self.update_region_and_region_id = \
            input('Введите область/город для поиска.\nИскомый текст должен быть на русском и длиннее 2 букв\n')
        # Выбор типов занятости
        print(f'\nТекущая занятость: {", ".join(self.update_employment_and_emp_rus[1])}')
        self.update_employment_and_emp_rus = \
            input('Выберите типы занятости:\n'
                  '1 - Полная\n'
                  '2 - Частичная\n'
                  '3 - Проектная\n'
                  '4 - Стажировка\n'
                  '5 - Отчистить список\n'
                  'Enter - Закончить выбор\n')
        # Выбор зп
        self.update_salary = \
            input('Введите ожидаемую зп или нажмите Enter для пропуска\n')
        # Выбор параметра только с зп
        self.update_only_w_salary = \
            input('Показывать вакансии без указания зп?\n1 - Да (по умолчанию)\n2 - Нет\n')
        # Выбор способа сортировки
        self.update_search_order = \
            input('Сортировать по:\n1 - Дате (по умолчанию)\n2 - Убыванию дохода\n')

        print(f'\n---НОВЫЕ ПАРАМЕТРЫ hh.ru---\n'
              f'Ключевые слова: {self.update_keywords[1]}\n'
              f'Регион: {self.update_region_and_region_id[1]}\n'
              f'Занятость: {", ".join(self.update_employment_and_emp_rus[1]).title()}\n'
              f'Ожидаемая зп: {self.update_salary} руб.\n'
              f'Только с указанием зп: {self.update_only_w_salary[1]}\n'
              f'Сортировка: {self.update_search_order[1]}\n')


class HHEmpSearchParams():
    """
    Класс выбора ключевых параметров для запросов работодателей hh.ru
    """

    # Текущая страница поиска
    page = 0

    def __init__(self, text: str = '', region: str = 'Москва', region_id: int = 1, only_with_vacancies: bool = True):
        """
        :param text: Название компании для получения списка компаний.
        :param region: Название региона.
        :param region_id: ID региона.
        """

        self.__text: str = text
        self.__region: str = region
        self.__region_id: int = region_id
        self.__only_with_vacancies: bool = only_with_vacancies

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__text},{self.__region},{self.__region_id})'

    def __str__(self):
        return f'Параметры поиска:\nТекст для поиска: {self.__text}, Область поиска: {self.__region}.' \
               f'Только с вакансиями: {self.__only_with_vacancies}'

    def __call__(self, *args, **kwargs) -> dict:
        """
        :return: Словарь для API запроса
        """
        return {'page': self.page,
                'per_page': 1,
                'text': self.update_search_txt,
                'area': self.update_region_and_region_id[0],
                'only_with_vacancies': self.__only_with_vacancies}

    @property
    def update_search_txt(self) -> str:
        return self.__text

    @update_search_txt.setter
    def update_search_txt(self, new_company_txt: str) -> None:
        new_company_txt: str = new_company_txt.casefold().strip()
        if new_company_txt != '':
            self.__text: str = new_company_txt
        elif len(new_company_txt) > 1:
            print('Неверный ввод')

    @property
    def update_region_and_region_id(self) -> tuple:
        return self.__region_id, self.__region

    @update_region_and_region_id.setter
    def update_region_and_region_id(self, new_region: str) -> None:
        new_region: str = new_region.casefold()
        results: dict = self.update_region_loop(new_region)
        # Если ничего не нашли - повторяем поиск
        if results is False:
            new_region: str = \
                input('Введите область/город для поиска.\n'
                      '\033[1m' + 'Искомый текст должен быть на русском и длиннее 2 букв\n' + '\033[0m').casefold()
            results = self.update_region_loop(new_region)
        print(f'Найдено {results[1]} результатов:')
        # Выводим результаты
        for idx, city in enumerate(results[0], start=1):
            print(f'{idx}. {city["text"]}')
            results[0][idx - 1].update({'Index': f'{idx}'})
        user_specified_region: str = input('Уточните область/город по номеру:\n')
        # Проверяем, что пользователь ввел значение для выбора области поиска из списка
        while not any(d['Index'] == user_specified_region for d in results[0]):
            print('Региона с таким номером нет в списке')
            user_specified_region: str = input('Уточните область/город по номеру:\n')
        # Обновляем ID для поиска
        self.__region_id: int = \
            list((entry['id'] for entry in results[0]
                  if entry['Index'] == user_specified_region))[0]
        # Обновляем текстовое обозначение области поиска
        self.__region = \
            list((entry['text'] for entry in results[0]
                  if entry['Index'] == user_specified_region))[0]

    @staticmethod
    def update_region_loop(new_region) -> tuple[dict, int] or bool:
        """
        Цикл для update_region_and_region_id()
        :return: Tuple со списком регионов и их кол-вом
        """
        while len(new_region) < 2 \
                or not all([data.isalpha() for data in new_region]) \
                or not bool(re.search('[а-яА-Я]', new_region)):
            print('Введите корректные данные')
            new_region: str = \
                input('Введите область/город для поиска.\n'
                      '\033[1m' + 'Искомый текст должен быть на русском и длиннее 2 букв\n' + '\033[0m').casefold()
        string: dict = {'text': new_region}
        number_of_found_regions: int = len(HeadHunterAPI.get_regions(params=string)['items'])
        if number_of_found_regions == 0:
            print('\nНайдено 0 результатов')
            return False
        correct_region: dict = HeadHunterAPI.get_regions(params=string)['items']
        return correct_region, number_of_found_regions

    @property
    def update_show_without_vac(self) -> bool:
        return self.__only_with_vacancies

    @update_show_without_vac.setter
    def update_show_without_vac(self, value) -> None:
        if value == '1':
            self.__only_with_vacancies = False
        elif value == '2':
            self.__only_with_vacancies = True
        else:
            print('Неверный ввод')
            self.__only_with_vacancies = True

    def hh_set_params_for_a_search(self) -> None:
        """
        Основная логика выбора параметров для поиска
        :return: экземпляр класса hh_search_params
        """
        # Выбор названия компании для поиска
        self.update_search_txt = \
            input('Введите название компании для поиска\n')
        if self.update_search_txt is False:
            print('Недействительный ввод')
            return
        # Выбор региона
        self.update_region_and_region_id = \
            input('Введите область/город для поиска.\nИскомый текст должен быть на русском и длиннее 2 букв\n')
        self.update_show_without_vac = \
            input("""Показывать компании без вакансий?\n1. Да\n2. Нет (по умолчанию)\n""")

        print(f'\n---НОВЫЕ ПАРАМЕТРЫ hh.ru---\n'
              f'Текст поиска: {self.update_search_txt}\n'
              f'Регион: {self.update_region_and_region_id[1]}\n'
              f'Только с активными вакансиями: {self.update_show_without_vac}\n')
