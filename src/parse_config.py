from os import path

import yaml


def get_data() -> dict:
    file_path = 'config.yml'
    if path.isfile(file_path) is True:
        with open(file_path) as file:
            date = yaml.safe_load(file)
            return date
    else:
        raise Exception('Отсутвует файл config.yml')


def get_host_zabbix() -> str:
    result = get_data()
    if result is not None:
        if 'connect' in result and 'host' in result['connect']:
            if type(result['connect']['host']) is str:
                return result['connect']['host']
            else:
                raise Exception(f'В файле config.yml параметр connect -> host не строка: {result["connect"]["host"]}')
        else:
            raise Exception('В файле config.yml не указан параметр connect -> host')
    else:
        raise Exception('В файле config.yml не указан параметр connect -> host')


def get_root_group() -> int | None:
    result = get_data()
    if result is not None:
        if 'permit' in result and 'root-group' in result['permit']:
            if type(result['permit']['root-group']) is str:
                return result['permit']['root-group']
            else:
                raise Exception(
                    f'В файле config.yml параметр permit -> root-group не строка: {result["permit"]["root-group"]}'
                )
        else:
            raise Exception('В файле config.yml не указан параметр permit -> root-group')
    else:
        raise Exception('В файле config.yml не указан параметр permit -> root-group')


def get_day_history_get() -> str:
    result = get_data()
    if result is not None:
        if 'history' in result and 'day-history-get' in result['history']:
            if type(result['history']['day-history-get']) is int:
                return result['history']['day-history-get']
            else:
                raise Exception(
                    f'В файле config.yml параметр history -> day-history-get не целое число: {result["history"]["day-history-get"]}'
                )
        else:
            raise Exception('В файле config.yml не указан параметр history -> day-history-get')
    else:
        raise Exception('В файле config.yml не указан параметр history -> day-history-get')


def get_limit_history_get() -> str:
    result = get_data()
    if result is not None:
        if 'history' in result and 'limit-history-get' in result['history']:
            if type(result['history']['limit-history-get']) is int:
                return result['history']['limit-history-get']
            else:
                raise Exception(
                    f'В файле config.yml параметр history -> limit-history-get не целое число: {result["history"]["limit-history-get"]}'
                )
        else:
            raise Exception('В файле config.yml не указан параметр history -> limit-history-get')
    else:
        raise Exception('В файле config.yml не указан параметр history -> limit-history-get')
