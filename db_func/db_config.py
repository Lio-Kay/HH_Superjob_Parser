"""
Этот файл содержит функцию для получения
конфигурации подключения к ДБ.
"""

from configparser import ConfigParser
from inspect import currentframe
import logging as log
import pathlib as pl

log.basicConfig(level=log.DEBUG,
                filename='/project_logs.log', filemode='w')


def config(filename=pl.Path.cwd() / 'db_func' / 'database.ini', section='postgresql') -> str:
    """
    :param filename: Название конфиг файла
    :param section: Секция поиска
    :return: Словарь с параметрами для подключения к дб
    """
    log.debug(f'Started {currentframe().f_code.co_name} func')
    parser = ConfigParser()
    parser.read(filename)
    db = []
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db.append(f'{param[0]}={param[1]}')
    else:
        log.exception(f'Section {section} is not found in the {filename} file.')
        raise Exception(f'Section {section} is not found in the {filename} file.')

    return ' '.join(db)
