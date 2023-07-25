from configparser import ConfigParser

import logging
from inspect import currentframe
import pathlib as pl


logging.basicConfig(level=logging.DEBUG, filename='/project_logs.log', filemode='w')


def config(filename=pl.Path.cwd() / 'db_func' / 'database.ini', section='postgresql') -> str:
    """
    :param filename: Название конфиг файла
    :param section: Секция поиска
    :return: Словарь с параметрами для подключения к дб
    """
    logging.debug(f'Started {currentframe().f_code.co_name} func')
    parser = ConfigParser()
    parser.read(filename)
    db = []
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db.append(f'{param[0]}={param[1]}')
    else:
        logging.exception(f'Section {section} is not found in the {filename} file.')
        raise Exception(f'Section {section} is not found in the {filename} file.')

    return ' '.join(db)
