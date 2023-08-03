# Парсер вакансий с сайтов hh.ru и superjob.ru

## Описание
CLI-программа на python для получения вакансий посредством API hh.ru и/или superjob.ru и последующим
сохранением в PostgreSQL. Пользователь может выбрать основные параметров поиска 
(ключевые слова в вакансии, регион поиска, тип занятости, ЗП, тип сортировки), добавлять вакансии и
работодателей в ЧС, сохранять все вакансии одного работодателя и работать с сохраненными данными
(сравнение зп, получения средней зп, поиск по ключевому слову).

## Пример получения вакансий
![usage_example.gif](readme_assets%2Fusage_example.gif)

## Описание структуры проекта
* api
  - api.py - Файл с классами для API запросов к разным платформам
* db_func
  - **database.ini - Необходимо создать для работы программы**
  - db_config.py - Файл для парсинга config файла database.ini в папке database_func
  - db_manipulation_func.py - db_func.py - Файл с классами для работы с postgres через psycopg2
* readme_assets - Файлы для README.md
* search_func
  - hh_search_func.py - Файл для получения данных от hh.ru, используя функции API запросов в api_requests.py
  - search_navigation.py - Файл для пользовательского выбора действия с вакансией/работодателем.
  - set_search_params.py - Файл для выбора поисковых платформ и точка запуска get_vacancies разных платформ.
  - superjob_search_func.py - Файл для получения данных от superjob.ru, используя функции API запросов в api_requests.py.
* search_params
  - hh_search_params.py - Файл с классами для выбора ключевых параметров для работы с API hh.ru
  - superjob_search_params.py - Файл с классами для выбора ключевых параметров для работы с API superjob.ru
* main.py - Меню и файл объединяющий всю логику
* project_logs.log - Создается при запуске, логгирует вызовы функций

## Инициализация проекта

**Для работы требуется PostgreSQL**

  ```sh
  git clone https://github.com/Lio-Kay/HH_Superjob_Parser
  ```

Создайте файл database.ini в папке database_func c данной структурой:

![usage_example2.png](readme_assets%2Fusage_example2.png)

Запустите через консоль:
  ```sh
  poetry update
  poetry run python main.py
  ```

## Технологии в проекте
Библиотеки:
* requests;
* psycopg2;
* forex-python;
* abc;
* pylint;
* inspect;
* re;
* json;
* os;
* pathlib.

Другие особенности:
* poetry вместо venv/pip;
* Написан на основе принципов SOLID;
* Отлов большинства ошибок взаимодействия пользователя с CLI;
* Логгирование действий пользователя;
* Линтинг через pylint;
* ДБ приведена к 3-ей нормальной форме.

## Возможные улучшения
* Написать unit-тесты на pytest;
* Добавить другие платформы;
* Расширить доступные фильтры;
* Расширить возможности работы с сохраненными данными.