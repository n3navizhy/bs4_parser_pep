import datetime as dt
import csv
import logging

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, PRETTY_MODE, FILE_MODE

LOGGING_FILE = 'Файл с результатами был сохранён: {path}'


def default_output(results, cli_args=None):
    # Печатаем список results построчно.
    for row in results:
        print(*row)


def pretty_output(results, cli_args=None):
    # Инициализируем объект PrettyTable.
    table = PrettyTable()
    # В качестве заголовков устанавливаем первый элемент списка.
    table.field_names = results[0]
    # Выравниваем всю таблицу по левому краю.
    table.align = 'l'
    # Добавляем все строки, начиная со второй (с индексом 1).
    table.add_rows(results[1:])
    # Печатаем таблицу.
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now}.csv'
    file_path = results_dir / file_name

    with open(file_path, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, dialect=csv.unix_dialect)
        writer.writerows(results)
    logging.info(LOGGING_FILE.format(path=file_path))


OUTPUTS = {
    PRETTY_MODE: pretty_output,
    FILE_MODE: file_output,
    None: default_output,
}


def control_output(results, cli_args=None):
    OUTPUTS.get(cli_args.output)(results, cli_args)
