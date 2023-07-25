from api.api_requests import SuperJobAPI

import re


class SuperjobSearchParams:
    """
    Класс выбора ключевых параметров для работы с API superjob.ru
    """

    page = 0

    def __init__(self, keyword: str = 'python', region: str = 'Москва', region_id: int = 4,
                 employment: int = 6, employment_rus: str = 'Полная', salary: int = 50_000,
                 only_w_salary: int = 1, only_w_salary_rus: str = 'Да', search_order: str = 'date',
                 search_order_rus: str = 'По дате публикации'):
        """
        :param keyword: Ключевые слова на языке запросов.
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

        self.__keyword: str = keyword
        self.__region: str = region
        self.__region_id: int = region_id
        self.__employment: int = employment
        self.__employment_rus: str = employment_rus
        self.__salary: int = salary
        self.__only_w_salary: int = only_w_salary
        self.__only_w_salary_rus: str = only_w_salary_rus
        self.__search_order: str = search_order
        self.__search_order_rus: str = search_order_rus

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__keyword},{self.__region},{self.__region_id}, {self.__employment},' \
               f'{self.__employment_rus},{self.__salary},{self.__only_w_salary},{self.__only_w_salary_rus},' \
               f'{self.__search_order}, {self.__search_order_rus})'

    def __str__(self):
        return f'Параметры поиска. Ключевое слово: {self.__keyword}, Область поиска: {self.__region},' \
               f'Тип занятости: {self.__employment}, Мин. зп {self.__salary},' \
               f'Только с указанием зп: {self.__only_w_salary_rus}, Сортировка по: {self.__search_order_rus}'

    @property
    def update_keyword(self) -> str:
        return self.__keyword

    @update_keyword.setter
    def update_keyword(self, new_keyword: str) -> None:
        new_keyword = new_keyword.casefold().strip()
        self.__keyword: str = new_keyword

    @property
    def update_region_and_region_id(self) -> tuple:
        return self.__region_id, self.__region

    @update_region_and_region_id.setter
    def update_region_and_region_id(self, new_region: str) -> None:
        print(new_region)
        print(self.update_region_and_region_id)
        new_region: str = new_region.casefold()
        results = self.update_region_loop(new_region)
        # Если ничего не нашли - повторяем поиск
        if results is False:
            new_region: str = \
                input('Введите область/город для поиска.\n'
                      '\033[1m' + 'Искомый текст должен быть на русском и длиннее 2 букв\n' + '\033[0m').casefold()
            results = self.update_region_loop(new_region)
        print(f'Найдено {results[1]} результатов:')
        # Выводим результаты
        for idx, city in enumerate(results[0], start=1):
            print(f'{idx}. {city["title"]}')
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
            list((entry['title'] for entry in results[0]
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
        number_of_found_regions = SuperJobAPI.get_regions(params=new_region)['total']
        if number_of_found_regions == 0:
            print(f'\nНайдено 0 результатов')
            return False
        correct_region = SuperJobAPI.get_regions(params=new_region)['objects']
        return correct_region, number_of_found_regions

    @property
    def update_employment_and_emp_rus(self) -> tuple[int, str]:
        return self.__employment, self.__employment_rus

    @update_employment_and_emp_rus.setter
    def update_employment_and_emp_rus(self, new_employment: str) -> None:
        results = self.update_employment_loop(new_employment)
        while results is False:
            new_employment: str = input('Выберите тип занятости:\n'
                                        '1 - Полный день\n'
                                        '2 - Неполный день\n'
                                        '3 - Сменный график\n'
                                        '4 - Частичная занятость\n'
                                        '5 - Временная работа\n'
                                        '6 - Вахтовым методом\n')
            results = self.update_employment_loop(new_employment)

    def update_employment_loop(self, new_employment: str) -> bool:
        """
        Цикл для update_employment_and_emp_rus()
        :return: False если ввод не поступил
        """
        if new_employment == '1':
            self.__employment_rus = 'Полный день'
            self.__employment = 6
            return True
        elif new_employment == '2':
            self.__employment_rus = 'Неполный день'
            self.__employment = 10
            return True
        elif new_employment == '3':
            self.__employment_rus = 'Сменный график'
            self.__employment = 12
            return True
        elif new_employment == '4':
            self.__employment_rus = 'Частичная занятость'
            self.__employment = 13
            return True
        elif new_employment == '5':
            self.__employment_rus = 'Временная работа'
            self.__employment = 7
            return True
        elif new_employment == '6':
            self.__employment_rus = 'Вахтовым методом'
            self.__employment = 9
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
            print('Некорректный ввод. Минимальная зп не установленна')
            self.__salary: int = 0
            return
        self.__salary = user_selected_salary

    @property
    def update_only_w_salary(self) -> tuple[int, str]:
        return self.__only_w_salary, self.__only_w_salary_rus

    @update_only_w_salary.setter
    def update_only_w_salary(self, new_only_w_salary: str) -> None:
        if new_only_w_salary != '2':
            self.__only_w_salary_rus = 'Да'
            self.__only_w_salary = 0
        elif new_only_w_salary == '2':
            self.__only_w_salary_rus = 'Нет'
            self.__only_w_salary = 1

    @property
    def update_search_order(self) -> tuple[str, str]:
        return self.__search_order, self.__search_order_rus

    @update_search_order.setter
    def update_search_order(self, new_search_order: str) -> None:
        if new_search_order != '2':
            self.__search_order_rus = 'По дате публикации'
            self.__search_order = 'date'
        elif new_search_order == '2':
            self.__search_order_rus = 'По убыванию дохода'
            self.__search_order = 'payment'

    def superjob_set_params_for_a_search(self) -> None:
        """
        Основная логика выбора параметров для поиска
        :return: Экземпляр класса с superjob_search_params
        """
        # Выбор ключевых слов для поиска
        self.update_keyword = input('Введите ключевое слово или нажмите Enter для пропуска\n')
        # Выбор региона
        self.update_region_and_region_id = \
            input('Введите область/город для поиска.\nИскомый текст должен быть на русском и длиннее 2 букв\n')
        # Выбор типа занятости для поиска
        self.update_employment_and_emp_rus =\
            input('Выберите тип занятости:\n'
                  '1 - Полный день\n'
                  '2 - Неполный день\n'
                  '3 - Сменный график\n'
                  '4 - Частичная занятость\n'
                  '5 - Временная работа\n'
                  '6 - Вахтовым методом\n')
        # Выбор мин. зп
        self.update_salary = \
            input('Введите минимальную зп или нажмите Enter для пропуска\n')
        # Выбор параметра только с зп
        self.update_only_w_salary = \
            input('Показывать вакансии без указания зп?\n1 - Да (по умолчанию)\n2 - Нет\n')
        # Выбор способа сортировки
        self.update_search_order = \
            input('Сортировать по:\n1 - Дате (по умолчанию)\n2 - Убыванию дохода\n')

        print(f'\n---НОВЫЕ ПАРАМЕТРЫ superjob.ru---\n'
              f'Ключевые слова: {self.update_keyword}\n'
              f'Регион: {self.update_region_and_region_id[1]}\n'
              f'Занятость: {self.update_employment_and_emp_rus[1]}\n'
              f'Ожидаемая зп: от {self.update_salary} руб.\n'
              f'Только с указанием зп: {self.update_only_w_salary[1]}\n'
              f'Сортировка: {self.update_search_order[1]}\n')
