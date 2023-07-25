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
              '2 - Больше не показывать компанию\n'
              '3 - Пропустить компанию\n'
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
                      '2 - Больше не показывать компанию\n'
                      '3 - Пропустить компанию\n'
                      f'4 - Закончить работу с текущей платформой\n')
