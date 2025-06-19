import json
import re
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
from jsonrpcclient import request

from config import API_TOKEN, HOST, day_history_get, limit_history_get, root_group, set_group_step_data
from data_class.data_zabbix import (
    GetParamZabbixModel,
)
from excel import f_save_xlsx
from http_base.request_base import BaseRequest
from zabbix.grops_handler import get_grops


def handler_get_hosts(items: str, group: str | None = None):
    list_items = items.split('/')
    req = BaseRequest(host=HOST, api_token=API_TOKEN)
    if group is not None:
        list_group = group.split('/')
        if len(list_group) > 0:
            try:
                [int(line) for line in list_group]
            except (ValueError, TypeError):
                print(f'Параметр группы может содержать только целые числа: {list_group}')

            state_error, list_error_group_permit, error_not_founr_group, list_group = get_grp(list_group)

            if state_error is False:
                srv_host = get_host_group_filter(list_group, req)
                if len(srv_host) > 0:
                    srv_items = get_items(srv_host, list_items, req)
                    if len(srv_items) > 0:
                        srv_history = get_history(srv_items, req)
                        if len(srv_history) > 0:
                            srv_host = match_result(srv_host, srv_items, srv_history)
                            handler_report(list_items, srv_host)
                        else:
                            print('За выбранный период врмени на сервере нет данных по искомым значениям')
                    else:
                        print(
                            f'На сервере в указанных группах: {list_group} нет искомых элементов данных: {list_items}'
                        )
                else:
                    print(f'На сервере в указанных группах: {list_group} нет услов сети')

            else:
                if len(list_error_group_permit) > 0:
                    print(f'Группы находятся вне зоны действия root_group: {list_error_group_permit}')
                if len(error_not_founr_group) > 0:
                    print(f'Групп нет на сервере: {error_not_founr_group}')
        else:
            print(f'Команда - группа введена ошибкой: {group}')
    else:
        pass


def match_result(srv_host, srv_items: list[dict], srv_history: list[list[dict]]) -> list[dict]:
    srv_items = match_items_history(srv_items, srv_history)

    for item in srv_items:
        index_host = search_host(srv_host, 'hostid', item['hostid'])
        if index_host != -1:
            if 'items' in srv_host[index_host]:
                srv_host[index_host]['items'].append(item)
            else:
                srv_host[index_host]['items'] = [item]
        else:
            raise Exception(f'Для элмента данных {item} не найден узел сети!!!')

    return srv_host


def match_items_history(srv_items: list[dict], srv_history: list[list[dict]]) -> list[dict]:
    # перебираем элементы данных
    for count_item, item in enumerate(srv_items):
        # проверяем статус элемента данных активрован/дективирован
        if item['status'] == '0':
            # ищем  в истории данные для конкртеного элемента данных
            index_history = search_history(srv_history, 'itemid', item['itemid'])
            if index_history != -1:
                trigger_history = 0
                for history in srv_history[index_history]:
                    if history['value'] != '0':
                        srv_items[count_item]['value'] = history['value']
                        srv_items[count_item]['clock'] = history['clock']
                        trigger_history = 1
                        break
                if trigger_history == 0:
                    srv_items[count_item]['value'] = srv_history[index_history][0]['value']
                    srv_items[count_item]['clock'] = srv_history[index_history][0]['clock']
            else:
                # нет данных для элемента данных
                srv_items[count_item]['value'] = 'Нет данных'
                srv_items[count_item]['clock'] = 'Нет данных'
        else:
            # эдемент данных деативирован
            srv_items[count_item]['value'] = 'Деактивирован'
            srv_items[count_item]['clock'] = 'Деактивирован'

    return srv_items


def get_grp(list_grops: list[str]) -> tuple[bool, list[str], str]:
    state_error = False
    list_group_tree = []
    # запрашиваем на сервере искомые гшруппы
    group_request = GetParamZabbixModel(
        output=['groupid', 'name'],
        filter={'groupid': list_grops},
    )
    group_server = get_grops(group_request)

    list_error_group_permit = []
    error_not_founr_group = ''
    if 'result' in group_server:
        trigger_group_permit = 0
        for src_group in list_grops:
            trigger_grp = 0
            for grp_srv in group_server['result']:
                if src_group == grp_srv['groupid']:
                    if grp_srv['name'] == root_group.replace('/', '') or grp_srv['name'].startswith(root_group) is True:
                        trigger_group_permit += 1
                    else:
                        list_error_group_permit.append([grp_srv['groupid'], grp_srv['name']])
                trigger_grp += 1

            if trigger_grp == 0:
                error_not_founr_group = error_not_founr_group + str(src_group) + ' '

        if trigger_group_permit != len(list_grops):
            state_error = True
        else:
            # если все требуемые группы есть на сервере запршиваем все их подгруппы
            search_group = [f'{group["name"]}/' for group in group_server['result']]
            grop_tree_request = GetParamZabbixModel(
                output=['groupid', 'name'],
                search={'name': search_group},
                sortfield='groupid',
                startSearch=True,
                searchByAny=True,
            )
            group_tree_server = get_grops(grop_tree_request)
            if 'result' in group_tree_server:
                list_group_tree = list_grops + [group['groupid'] for group in group_tree_server['result']]
            elif 'error' in group_server:
                raise Exception(f'ошибка group_tree_server: {group_tree_server["error"]}')
            else:
                raise Exception(f'не известный результат работы get_hadler_hosr.get_grops, result: {group_tree_server}')

    elif 'error' in group_server:
        raise Exception(f'ошибка group_server: {group_server["error"]}')
    else:
        raise Exception(f'не известный результат работы get_hadler_hosr.get_grops, result: {group_server}')

    return state_error, list_error_group_permit, error_not_founr_group, list_group_tree


def get_items(host_srv: list[dict], items: list[str], req: BaseRequest) -> tuple[bool, list[str], str]:
    result = []
    # получаем список узлов сети по группам

    # if len(host_srv) > 0:
    step_data = set_group_step_data
    host_srv_ids = [host['hostid'] for host in host_srv]
    for i in range(0, len(host_srv_ids), step_data):
        items_filter = GetParamZabbixModel(
            output=['hostid', 'name', 'itemid', 'value_type', 'status'],
            hostids=host_srv_ids[i : i + step_data],
            filter={'name': items},
            searchByAny=True,
        )
        params = request('item.get', params=items_filter.model_dump(exclude_none=True))
        hosts = req.post_request_with_token(params)
        if hosts.status is True:
            data_request = json.loads(hosts.data)
            if 'result' in data_request:
                result = result + data_request['result']
            else:
                raise Exception(f'Венулись не корректные данные: {data_request}')
        else:
            raise Exception(f'Ошибка: {hosts.error}')
    result = sorted(result, key=lambda item: int(item['itemid']))

    return result


def get_history(list_items: list[dict], req: BaseRequest):
    result = []
    step_data = set_group_step_data
    time_from = int((datetime.now(timezone.utc) - timedelta(days=day_history_get)).timestamp())
    for i in range(0, len(list_items), step_data):
        temp_req_param = []
        for items in list_items[i : i + step_data]:
            if items['status'] == '0':
                temp_param = {
                    'output': 'extend',
                    'history': int(items['value_type']),
                    'itemids': items['itemid'],
                    'sortfield': 'clock',
                    'sortorder': 'DESC',
                    'limit': limit_history_get,
                    'time_from': time_from,
                }
                temp_req_param.append(request('history.get', params=temp_param))
        if len(temp_req_param) > 0:
            # params = request('history.get', params=temp_req_param)
            history = req.post_request_with_token(temp_req_param)
            if history.status is True:
                data_request = json.loads(history.data)
                for history in data_request:
                    if 'result' in history:
                        history_id = int(history['id'])
                        if history_id < history['id']:
                            print(f'history_id: {history_id} < history["id"] {history["id"]}')
                        if len(history['result']) > 0:
                            result.append(history['result'])
                    else:
                        raise Exception(f'Венулись не корректные данные: {data_request}')
            else:
                raise Exception(f'Ошибка: {history.error}')

    return result


def get_host_group_filter(data: list[str], req: BaseRequest) -> list[dict]:
    """
    функция получает список имен групп и по нему формиурется запрос
    запрос разбиывается на чанки размером set_group_step_data
    возвращается id и имя узла сети
    """
    result = []
    # создается класс для обращения по http и отпарвялется запрос

    # set_group_step_data - указывается в config файле
    step_data = set_group_step_data
    # делим при необоходимости список заданий на чанки размером step_data
    for i in range(0, len(data), step_data):
        # создаем запрос к серверу на вывод всех узлов сети из задания
        host_filter = GetParamZabbixModel(
            output=['hostid', 'host'], groupids=data[i : i + step_data], selectInterfaces='extend', sortfield='hostid'
        )
        params = request('host.get', params=host_filter.model_dump(exclude_none=True))
        hosts = req.post_request_with_token(params)
        if hosts.status is True:
            data_request = json.loads(hosts.data)
            if 'result' in data_request:
                for host in data_request['result']:
                    if len(host['interfaces']) > 0:
                        host['interfaces'] = host['interfaces'][0]['ip']
                    else:
                        host['interfaces'] = 'Нет интерфейса'
                    result.append(host)
            else:
                raise Exception(f'Венулись не корректные данные: {data_request}')
        else:
            raise Exception(f'Ошибка: {hosts.error}')

    result = pd.DataFrame(result).drop_duplicates().to_dict('records')
    result = sorted(result, key=lambda host: int(host['hostid']))
    return result


def search_history(arr, key, value):
    """
    Бинарный поиск в списке списков словарей по ключу.

    :param arr: Отсортированный список словарей
    :param key: Ключ, по которому ищем
    :param value: Искомое значение
    :return: Индекс найденного элемента или -1
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        try:
            mid_val = arr[mid][0][key]
        except Exception as ex:
            print(ex)
            print(arr[mid])
            print(key)
            print(len(arr))
            print(arr)
            sys.exit(0)

        if mid_val == value:
            return mid
        elif mid_val < value:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def search_host(arr, key, value):
    """
    Бинарный поиск в списке словарей по ключу.

    :param arr: Отсортированный список словарей
    :param key: Ключ, по которому ищем
    :param value: Искомое значение
    :return: Индекс найденного элемента или -1
    """
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = (left + right) // 2
        mid_val = arr[mid][key]

        if mid_val == value:
            return mid
        elif mid_val < value:
            left = mid + 1
        else:
            right = mid - 1

    return -1


def handler_report(list_items: list[str], srv_host: list[dict]):
    header = ['№ п/п', 'Имя узла', 'IP узла']
    len_header_src = len(header)
    index_item = {}
    for items in list_items:
        header.append(f'{items}_дата')
        header.append(f'{items}_значение')
        index_item[items] = len(header) - 2

    data = []

    for count_host, host in enumerate(srv_host):
        temp_host = [
            count_host + 1,
            host['host'],
            host['interfaces'],
        ]

        for _ in range(len(header) - len_header_src):
            temp_host.append('')

        if 'items' in host:
            for item_host in host['items']:
                index_item_host = index_item[item_host['name']]
                try:
                    date_item = datetime.fromtimestamp(int(item_host['clock']))
                    temp_host[index_item_host] = date_item.strftime('%d.%m.%Y %H:%M:%S')
                except Exception:
                    temp_host[index_item_host] = item_host['clock']
                value_item = converter_value_item(item_host['value'])
                temp_host[index_item_host + 1] = value_item
        else:
            for i in range(len_header_src, len(header), 2):
                temp_host[i] = 'У узла нет элемента данных'
                temp_host[i + 1] = 'У узла нет элемента данных'

        for count_t_host, t_host in enumerate(temp_host[len_header_src:]):
            if t_host == '':
                temp_host[count_t_host + len_header_src] = 'У узла нет элемента данных'

        data.append(temp_host)

    f_save_xlsx('GET_HOST_HANDLER', 'results', header, data)


def converter_value_item(value_in: str) -> int | float | str:
    try:
        value_in = value_in.replace(',', '.')
        pattern = r'^[+-]?\d*\.{1}\d+$'
        if re.fullmatch(pattern, value_in) is not None:
            return round(float(value_in), 4)
        else:
            return int(value_in)

    except Exception:
        return value_in
