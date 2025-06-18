import argparse


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        description='Скрипт для автоматизации занесения/изменения/удаление и вычитки данных из Zabbix'
    )

    parser.add_argument(
        '-t', '--type', help='тип запуска', required=True, type=str, choices=['get_host', 'host', 'group']
    )

    parser.add_argument(
        '-ghi',
        '--get_host_items',
        help='для команды group: перечень элементов данных, которые нужно получить при вычитки данных',
        required=False,
        type=str,
    )

    parser.add_argument(
        '-ghg',
        '--get_host_group',
        help='для команды group: перечень групп для вычитки данных',
        required=False,
        type=str,
    )

    args = parser.parse_args()
    args = vars(args)

    return args
