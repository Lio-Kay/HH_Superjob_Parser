import logging
from inspect import currentframe
import pathlib
import psycopg2 as db
from db_func.db_config import config

logging.basicConfig(level=logging.DEBUG, filename=pathlib.Path.cwd() / 'project_logs.log', filemode='w')

db_config_initial = config()
db_config = db_config_initial.replace('postgres', 'hh_superjob_data', 1)


class DBCreator:
    """
    Класс для создания БД и таблиц
    """

    @classmethod
    def create_database(cls) -> None:
        """
        Создает БД
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        conn = db.connect(db_config_initial)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'hh_vacancies'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f'CREATE DATABASE hh_vacancies')
        conn.close()
        logging.debug(f'Created DB hh_vacancies')

    @classmethod
    def create_tables(cls) -> None:
        """
        Создает таблицы employers, vacancies, blacklisted
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        conn = db.connect(db_config)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS employers(
        id INT,
        name VARCHAR(100) NOT NULL,
        industry VARCHAR(50),
        vac_count INT,
        url VARCHAR(100) NOT NULL,
        PRIMARY KEY(id))
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS vacancies(
        id INT,
        employer_id INT NOT NULL,
        name VARCHAR(100) NOT NULL,
        area VARCHAR(100),
        salary INT,
        currency VARCHAR(100),
        gross BOOL,
        schedule VARCHAR(100),
        requirement TEXT,
        responsibility TEXT,
        url VARCHAR(100) NOT NULL,
        PRIMARY KEY(id),
        CONSTRAINT fk_employers FOREIGN KEY(employer_id) REFERENCES employers(id))
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS blacklisted_employers(
        id INT,
        blacklisted BOOL,
        PRIMARY KEY(id))
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS blacklisted_vacancies(
        id INT,
        blacklisted BOOL,
        PRIMARY KEY(id))
        ''')
        conn.close()
        logging.debug(f'Created DB\'s tables')


class DBManager:
    """
    Класс для добавления и получения данных из БД
    """

    @classmethod
    def save_vacancy_to_db(cls, vac_id: int, employer_id: int, name: str, area: str, salary: int,
                           currency: str, gross: bool, schedule: str, requirement: str,
                           responsibility: str, url: str) -> None:
        """
        Добавить вакансию в БД
        :param vac_id: ID вакансии
        :param employer_id: ID компании
        :param name: Название вакансии
        :param area: Местоположение
        :param salary: ЗП
        :param currency: Валюта
        :param gross: С учетом налогов
        :param schedule: Тип занятости
        :param requirement: Требования
        :param responsibility: Обязанности
        :param url: Ссылка на вакансию
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO vacancies(
                id, employer_id, name, area, salary, currency, gross, schedule, 
                requirement, responsibility, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                            (vac_id, employer_id, name, area, salary, currency, gross, schedule,
                             requirement, responsibility, url))
        conn.close()
        logging.debug(f'Added vacancy {name}, URL: {url} to DB')

    @classmethod
    def save_employer_to_db(cls, comp_id: int, name: str, industry: str, vac_count: int, url: str) -> None:
        """
        Добавить компанию в список отслеживания
        :param comp_id: ID компании
        :param name: Название компании
        :param industry: Отрасль деятельности
        :param vac_count: Кол-во вакансий у компании
        :param url: Ссылка на компанию
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''
                INSERT INTO employers(
                id, name, industry, vac_count, url)
                VALUES(%s, %s, %s, %s, %s)
                ''', (comp_id, name, industry, vac_count, url))
        conn.close()
        logging.debug(f'Added company {name}, URL: {url} to DB')

    @classmethod
    def blacklist_vacancy(cls, vac_id: int, blacklisted: bool = True) -> None:
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO blacklisted_vacancies(
                        id, blacklisted)
                        VALUES (%s, %s)''',
                            (vac_id, blacklisted))
        conn.close()
        logging.debug(f'Added vacancy {vac_id}, Blacklisted: {blacklisted} to blacklist')

    @classmethod
    def blacklist_employer(cls, emp_id: int, blacklisted: bool = True) -> None:
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO blacklisted_employers(
                            id, blacklisted)
                            VALUES (%s, %s)''',
                            (emp_id, blacklisted))
        conn.close()
        logging.debug(f'Added employer {emp_id}, Blacklisted: {blacklisted} to blacklist')

    @classmethod
    def check_blacklisted_vacancies(cls, vac_id: int) -> bool:
        """
        Проверяет, есть ли вакансия в ЧС
        :param vac_id: ID вакансии для проверки наличия в ЧС
        :return: True если вакансия в ЧС
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM blacklisted_vacancies WHERE id = {vac_id}''')
                if cur.fetchall():
                    logging.debug(f'Vacancy {vac_id} is in the blacklist')
                    return True
        conn.close()
        logging.debug(f'Vacancy {vac_id} is not in the blacklist')

    @classmethod
    def check_blacklisted_employer(cls, emp_id: int):
        """
        Проверяет, есть ли компания в ЧС
        :param emp_id: ID компании для проверки наличия в ЧС
        :return: True если компания в ЧС
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM blacklisted_employers WHERE id = {emp_id}''')
                if cur.fetchall():
                    logging.debug(f'Company {emp_id} is in the blacklist')
                    conn.close()
                    return True
        logging.debug(f'Company {emp_id} is not in the blacklist')

    @classmethod
    def remove_vacancy_from_blacklist(cls) -> None:
        """
        Удалить вакансию из ЧС
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        vac_id: str = input('Введите ID вакансии для удаления\n').strip()
        if vac_id == '':
            print('Неверный ввод')
            logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
            return
        try:
            vac_id: int = int(vac_id)
        except TypeError:
            print('Неверный ввод')
            logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
            return
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM blacklisted_vacancies WHERE id = '{vac_id}'")
                if cur.fetchall():
                    cur.execute(f"DELETE FROM blacklisted_vacancies WHERE id = '{vac_id}'")
                    print('Удаление из ЧС успешно')
                    logging.debug(f'Deleted {vac_id} from blacklist')
                else:
                    print('Такого ID нет в списке')
                    logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
        conn.close()

    @classmethod
    def remove_employer_from_blacklist(cls) -> None:
        """
        Удалить компанию из ЧС
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        emp_id: str = input('Введите ID компании для удаления\n').strip()
        if emp_id == '':
            print('Неверный ввод')
            logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
            return
        try:
            emp_id: int = int(emp_id)
        except TypeError:
            print('Неверный ввод')
            logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
            return
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM blacklisted_employers WHERE id = '{emp_id}'")
                if cur.fetchall():
                    cur.execute(f"DELETE FROM blacklisted_employers WHERE id = '{emp_id}'")
                    print('Удаление из ЧС успешно')
                    logging.debug(f'Deleted {emp_id} from blacklist')
                else:
                    print('Такого ID нет в списке')
                    logging.debug(f'Finished {currentframe().f_code.co_name} func without result')
        conn.close()
    
    @classmethod
    def check_vacancy_in_db(cls, vac_id: int) -> bool:
        """
        :param vac_id: ID вакансии для проверки наличия в БД
        :return: True если вакансия уже есть
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM vacancies WHERE id = {vac_id}''')
                if cur.fetchall():
                    logging.debug(f'Vacancy {vac_id} is in the list')
                    return True
        conn.close()
        logging.debug(f'Vacancy {vac_id} is not in the list')

    @classmethod
    def check_employer_in_db(cls, emp_id: int) -> bool:
        """
        :param emp_id: ID компании для проверки наличия в БД
        :return: True если вакансия уже есть
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM employers WHERE id = {emp_id}''')
                if cur.fetchall():
                    logging.debug(f'Employer {emp_id} is in the list')
                    return True
        conn.close()
        logging.debug(f'Employer {emp_id} is not in the list')

    @classmethod
    def get_companies_and_vacancies_count(cls) -> None:
        """
        Получить список компаний и кол-во вакансий компании
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM employers''')
                for idx, company in enumerate(cur.fetchall(), start=1):
                    print(f"""№{idx}\nID: {company[0]}. Компания: {company[1]}. Кол-во вакансий: {company[2]}.""")
        conn.close()
        logging.debug(f'Got list of vacancies and their count')

    @classmethod
    def get_all_vacancies(cls) -> None:
        """
        Получить список всех вакансий
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT * FROM vacancies''')
                for idx, vacancy in enumerate(cur.fetchall(), start=1):
                    cur.execute(f"SELECT name FROM employers WHERE id='{vacancy[1]}'")
                    comp_name = cur.fetchall()
                    print(f"""№{idx}\n Компания: {comp_name[0][0]} Вакансия: {vacancy[2]}.
                    ЗП: {vacancy[4]}. URL: {vacancy[10]}""")
        conn.close()
        logging.debug(f'Got all vacancies')

    @classmethod
    def get_avg_salary(cls) -> None:
        """
        Получить среднюю зп по вакансиям
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT AVG(salary) FROM vacancies''')
                print(f'Средняя зп вакансий: {round(cur.fetchall()[0][0], 0)}')
        conn.close()
        logging.debug(f'Got avg salary')

    @classmethod
    def get_vacancies_with_higher_salary(cls) -> None:
        """
        Получить вакансии с зп выше средней
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f'''SELECT *, salary FROM vacancies WHERE salary > (SELECT AVG(salary) FROM vacancies)''')
                result = cur.fetchall()
                for idx, vacancy in enumerate(result, start=1):
                    cur.execute(f"SELECT name FROM employers WHERE id='{vacancy[1]}'")
                    comp_name = cur.fetchall()
                    print(f"№{idx}\n"
                          f"Компания: {comp_name[0][0]} Вакансия: {vacancy[2]}. ЗП: {vacancy[4]}. URL: {vacancy[10]}")
        conn.close()
        logging.debug(f'Got vacancies with high salary')

    @classmethod
    def get_vacancies_with_keyword(cls) -> None:
        """
        Получить вакансии по ключевому слову в названии
        """
        logging.debug(f'Started {currentframe().f_code.co_name} func')
        vacancy_keyword: str = input('Введите ключевое слово для поиска\n')
        with db.connect(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM vacancies WHERE name LIKE '%{vacancy_keyword}%'")
                result = cur.fetchall()
                if result:
                    for idx, vacancy in enumerate(result, start=1):
                        cur.execute(f"SELECT name FROM employers WHERE id='{vacancy[1]}'")
                        comp_name = cur.fetchall()
                        print(f"№{idx}\nКомпания: {comp_name[0][0]} Вакансия: {vacancy[2]}."
                              f"ЗП: {vacancy[4]}. URL: {vacancy[10]}")
                        logging.debug(f'Got vacancies with keyword {vacancy_keyword}')
        conn.close()
