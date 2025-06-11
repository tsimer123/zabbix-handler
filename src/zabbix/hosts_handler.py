import json
import re

from jsonrpcclient import request

from config import (
    API_TOKEN,
    HOST,
    command_extended_parameters,
    command_hosts,
    command_hosts_not_present,
    command_hosts_present,
    header_results_host,
    hosts_file,
    root_group,
    set_group_step_data,
)
from data_class.data_zabbix import (
    GetParamZabbixModel,
    GroupsHostZabbixModel,
    InterfacesHostZabbixModel,
    ParamCreateHostZabbixModel,
    TemplatesHostZabbixModel,
)
from excel import f_save_xlsx, open_excel
from http_base.request_base import BaseRequest
from zabbix.base_func import is_valid_ipv4, transliterate_host
from zabbix.grops_handler import get_grops
from zabbix.templates_handler import get_templates


def handler_hosts():
    # открывается excel файл
    data = open_excel(hosts_file)
    if data is not None:
        if len(data) > 1:
            data = copy_excel_to_format(data[1:])
            data, state_error = valid_group(data)
            if state_error is False:
                f_save_xlsx('HOST_HANDLER', 'results', header_results_host, data)
            else:
                # при наличии ошибок валидации формуруется отчет в excel файле
                f_save_xlsx('HOST_HANDLER', 'results', header_results_host, data)
        else:
            print('Ошибка - файл с заданием пустой')


def copy_excel_to_format(data: list[list]):
    for task in data:
        if len(task) < 5:
            count_len = 5 - len(task)
            for _ in range(count_len):
                task.append(None)

    return data


def valid_group(data: list[list]) -> tuple[list[list], bool]:
    list_name_host = []
    state_error = False
    for count_host, host in enumerate(data):
        # проверяем команду на разрешенные
        if host[0] is not None and host[0] in command_hosts:
            # проверяем имя узла на допустимое
            if host[1] is not None and re.fullmatch(r'[a-zA-Z0-9а-яА-Я\_\.\-\/]+', host[1]):
                # проверяем ip адрес на валидность
                if host[0] in command_extended_parameters and host[2] is not None:
                    if is_valid_ipv4(host[2]) is True:
                        # проверяем шаблоны на валидность
                        # не пустой
                        if host[3] is not None:
                            # получаем список шаблонов
                            temp_tempalate = str(host[3]).split(';')
                            trigger_tmplt = 0
                            for template in temp_tempalate:
                                # проверяется каждый шаблон на то что он целое число
                                if re.fullmatch(r'\d+', str(template)) is not None:
                                    trigger_tmplt += 1
                            # проверятся равно ли количество валидных шаблонов количеству шаблонов
                            if trigger_tmplt == len(temp_tempalate):
                                # проверяются группы на валидность
                                if host[4] is not None:
                                    # получаем список групп
                                    temp_groups = str(host[4]).split(';')
                                    trigger_group = 0
                                    # проверяется каждую группу на коректность написания
                                    for group in temp_groups:
                                        if re.fullmatch(r'\d+', str(group)) is not None:
                                            trigger_group += 1
                                    if trigger_group == len(temp_groups):
                                        # если все данные валидные, то добаввляем имя узла сети в список для запроса наличия
                                        # таких узлов на сервере
                                        list_name_host.append(transliterate_host(host[1]))
                                    else:
                                        # имя группы не валидны
                                        data[count_host].append(False)
                                        data[count_host].append(
                                            'Имя группы может содержать: a-z, A-Z, 0-9, а-я, А-Я, -, /'
                                        )
                                        data[count_host].append('Отмена')
                                        state_error = True
                                else:
                                    if host[0] in command_extended_parameters:
                                        # имя группы не валидны
                                        data[count_host].append(False)
                                        data[count_host].append('Имя группы не может быть пустым')
                                        data[count_host].append('Отмена')
                                        state_error = True
                                    else:
                                        list_name_host.append(transliterate_host(host[1]))
                            else:
                                # шаблон не валидный
                                data[count_host].append(False)
                                data[count_host].append(f'id шаблона может быть только число: {host[3]}')
                                data[count_host].append('Отмена')
                                state_error = True
                        else:
                            if host[0] in command_extended_parameters:
                                # шаблон не валидный
                                data[count_host].append(False)
                                data[count_host].append('id шаблона не может быть пустым')
                                data[count_host].append('Отмена')
                                state_error = True
                            else:
                                list_name_host.append(transliterate_host(host[1]))
                    else:
                        # ip адрес не валидный
                        data[count_host].append(False)
                        data[count_host].append(f'Не верный формат ip: {host[2]} или пусто')
                        data[count_host].append('Отмена')
                        state_error = True
                else:
                    if host[0] in command_extended_parameters:
                        data[count_host].append(False)
                        data[count_host].append('Поле ip не может быть пустым')
                        data[count_host].append('Отмена')
                        state_error = True
                    else:
                        list_name_host.append(transliterate_host(host[1]))
            else:
                # имя хоста не валидный
                data[count_host].append(False)
                data[count_host].append(
                    'Имя узла сети может содержать: a-z, A-Z, 0-9, а-я, А-Я, _, ., -, /, и не может быть пустым'
                )
                data[count_host].append('Отмена')
                state_error = True
        else:
            # команда отсутствует в списке разрешенных
            data[count_host].append(False)
            data[count_host].append(f'Не валидная команда: {host[0]}')
            data[count_host].append('Отмена')
            state_error = True

    # если нет ошибок с записью задания
    if state_error is False:
        data, state_error = get_host_valid(data, list_name_host)

    # если нет ошибок с записью задания и наличие хостов на сервере валидно
    # проверяется валидность групп и шаблонов
    if state_error is False:
        list_tmpt = []
        list_grp = []
        for task in data:
            if task[0] in command_extended_parameters:
                temp_tempalate = str(task[3]).split(';')
                for template in temp_tempalate:
                    list_tmpt.append(template)
            if task[0] in command_extended_parameters:
                temp_groups = str(task[4]).split(';')
                for grop in temp_groups:
                    list_grp.append(grop)

        if len(list_tmpt) > 0:
            list_tmpt = list(set(list_tmpt))
            data, state_error = get_tmpt(data, list_tmpt)

        if state_error is False and len(list_grp) > 0:
            list_grp = list(set(list_grp))
            data, state_error = get_grp(data, list_grp)

    return data, state_error


def get_host_name_filter(data: GetParamZabbixModel) -> list[dict]:
    """
    функция получает параметр для запроса групп на сервер и возвращает результат в фрмате словаря,
    если при запросе возникла ошибка то вызывается исключение
    """
    result = []
    # создается класс для обращения по http и отпарвялется запрос
    req = BaseRequest(host=HOST, api_token=API_TOKEN)
    # set_group_step_data - указывается в config файле
    step_data = set_group_step_data
    # делим при необоходимости список заданий на чанки размером step_data
    for i in range(0, len(data), step_data):
        # создаем запрос к серверу на вывод всех узлов сети из задания
        host_filter = GetParamZabbixModel(
            output=['hostid', 'host'],
            filter={'host': data[i : i + step_data]},
        )
        params = request('host.get', params=host_filter.model_dump(exclude_none=True))
        hosts = req.post_request_with_token(params)
        if hosts.status is True:
            data_request = json.loads(hosts.data)
            if 'result' in data_request:
                result = result + data_request['result']
            else:
                raise Exception(f'Венулись не корректные данные: {data_request}')
        else:
            raise Exception(f'Ошибка: {hosts.error}')

    return result


def get_host_valid(data: list[list], list_name_host: list[str]) -> tuple[list[list], bool]:
    state_error = False
    # запрос к серверву
    hosts = get_host_name_filter(list_name_host)
    # перебор задания
    for count_host, host_in in enumerate(data):
        trigger_task = 0
        # перебор ответа от сервера
        for host_srv in hosts:
            # сравнение имени хоста из задания в траслите с хостами на сервере
            if transliterate_host(host_in[1]) == host_srv['host']:
                # если в задании команада add то ошибика
                if host_in[0] in command_hosts_not_present:
                    data[count_host].append(False)
                    data[count_host].append(f'Такой хост уже существует: {host_srv}')
                    data[count_host].append('Отмена')
                    data[count_host].append(host_srv['hostid'])
                    state_error = True
                # если в задании команада del, update, active и то отмечаем как рабочую
                if host_in[0] in command_hosts_present:
                    data[count_host].append(True)
                    data[count_host].append('')
                    data[count_host].append('')
                    data[count_host].append(host_srv['hostid'])
                trigger_task = 1
                break
        # если хоста из задания нет на серевере
        if trigger_task == 0:
            # если в задании команада add то успех
            if host_in[0] in command_hosts_not_present:
                data[count_host].append(True)
                data[count_host].append('')
                data[count_host].append('')
            # если в задании команада del, update, active и то отмечаем как ошибку
            if host_in[0] in command_hosts_present:
                data[count_host].append(False)
                data[count_host].append(f'Хост отсутствует на сервере: {host_in[1]}')
                data[count_host].append('Отмена')
                state_error = True

    return data, state_error


def get_tmpt(data: list[list], list_tmpl: list[str]) -> tuple[list[list], bool]:
    state_error = False
    tmplt_request = GetParamZabbixModel(output='templateid', templateid=list_tmpl)
    tmplts_server = get_templates(tmplt_request)
    if 'result' in tmplts_server:
        list_temp_temlate = [tmlt_server['templateid'] for tmlt_server in tmplts_server['result']]
        for count_host, host in enumerate(data):
            if host[0] in command_extended_parameters and host[3] is not None:
                temp_tempalate = str(host[3]).split(';')
                trigger_temp_tempalate = 0
                list_error_tmplt = []
                for template in temp_tempalate:
                    if template in list_temp_temlate:
                        trigger_temp_tempalate += 1
                    else:
                        list_error_tmplt.append(template)
                if trigger_temp_tempalate != len(temp_tempalate):
                    data[count_host][5] = False
                    data[count_host][6] = 'На сервере нет указанного шаблона: ' + ','.join(list_error_tmplt)
                    data[count_host][7] = 'Отмена'
                    state_error = True
    elif 'error' in tmplts_server:
        raise Exception(f'ошибка tmplts_server: {tmplts_server["error"]}')
    else:
        raise Exception(f'не известный результат работы handler_grop.get_grops, result: {tmplts_server}')

    return data, state_error


def get_grp(data: list[list], list_grops: list[str]) -> tuple[list[list], bool, list[dict]]:
    state_error = False
    grop_request = GetParamZabbixModel(
        output=['groupid', 'name'],
        filter={'groupid': list_grops},
    )
    group_server = get_grops(grop_request)

    if 'result' in group_server:
        for count_host, host in enumerate(data):
            list_error_group_permit = []
            if host[0] in command_extended_parameters and host[4] is not None:
                temp_grops = str(host[4]).split(';')
                trigger_temp_group = 0
                for tmp_group in temp_grops:
                    for grp_server in group_server['result']:
                        if tmp_group == grp_server['groupid']:
                            if grp_server['name'].startswith(root_group.replace('/', '')) is False:
                                list_error_group_permit.append(grp_server['name'])
                            trigger_temp_group += 1
                            break
                if len(list_error_group_permit) > 0:
                    data[count_host][5] = False
                    data[count_host][6] = 'Доступ к данным группам запрещен: ' + ','.join(list_error_group_permit)
                    data[count_host][7] = 'Отмена'
                    state_error = True
                if trigger_temp_group != len(temp_grops):
                    data[count_host][5] = False
                    data[count_host][6] = 'На сервере нет указанной группы'
                    data[count_host][7] = 'Отмена'
                    state_error = True
    elif 'error' in group_server:
        raise Exception(f'ошибка group_server: {group_server["error"]}')
    else:
        raise Exception(f'не известный результат работы handler_grop.get_grops, result: {group_server}')

    return data, state_error


def handler_host_comand(data: list[list]) -> list[list]:
    create_host_params = []
    delete_host_params = []
    update_host_params = []
    active_host_params = []
    deactive_host_params = []

    create_index = []
    delete_index = []
    update_index = []
    active_index = []
    deactive_index = []

    # сотируются данные по типам задач
    for index_t, task in enumerate(data):
        if task[0] == 'add':
            # создаются параметры для добавления узла сети
            temp_param_add = create_extended_parameters(task)
            create_host_params.append(temp_param_add.model_dump(exclude_none=True))
            # создаем список индексов в общем списке по каждой оперции
            create_index.append(index_t)

        # if task[0] == 'update':
        #     # создаются параметры для измнения узла сети

        #     update_host_params.append(temp_param_upd.model_dump(exclude_none=True))
        #     # создаем список индексов в общем списке по каждой оперции
        #     update_index.append(index_t)

        if task[0] == 'del':
            delete_host_params.append(str(task[8]))
            delete_index.append(index_t)

        if task[0] == 'active':
            active_host_params.append({'hostid': str(task[8]), 'status': 0})
            active_index.append(index_t)

        if task[0] == 'deactive':
            deactive_host_params.append({'hostid': str(task[8]), 'status': 1})
            deactive_index.append(index_t)

    if len(create_host_params) > 0:
        # отправляем отстортированные задачи далее для проведжения опрераций на сервере
        create_group = set_host('host.create', create_host_params)
        # сопоставляем полученные данные от сервера с входными данными
        data = match_task(data, create_group, create_index)

    if len(delete_host_params) > 0:
        # отправляем отстортированные задачи далее для проведжения опрераций на сервере
        delete_group = set_host('host.delete', delete_host_params)
        # сопоставляем полученные данные от сервера с входными данными
        data = match_task(data, delete_group, delete_index)

    if len(active_host_params) > 0:
        # отправляем отстортированные задачи далее для проведжения опрераций на сервере
        active_group = set_host('host.update', active_host_params)
        # сопоставляем полученные данные от сервера с входными данными
        data = match_task(data, active_group, active_index)

    if len(deactive_index) > 0:
        # отправляем отстортированные задачи далее для проведжения опрераций на сервере
        deactive_group = set_host('host.update', deactive_index)
        # сопоставляем полученные данные от сервера с входными данными
        data = match_task(data, deactive_group, deactive_index)

    return data


def create_extended_parameters(task: list) -> ParamCreateHostZabbixModel:
    # создаются параметры для добавления узла сети
    # создается параметр с интерфейсами
    interface = [InterfacesHostZabbixModel(ip=task[2])]

    # создается параметр с группами
    groups = []
    temp_grops = str(task[4]).split(';')
    for tmp_group in temp_grops:
        groups.append(GroupsHostZabbixModel(groupid=tmp_group))

    # создается параметр с шаблонами
    templates = []
    temp_tempalate = str(task[3]).split(';')
    for template in temp_tempalate:
        templates.append(TemplatesHostZabbixModel(templateid=template))

    result_param = ParamCreateHostZabbixModel(
        host=transliterate_host(task[1]), interface=interface, groups=groups, templates=templates
    )

    return result_param


def set_host(command: str, data: list[dict] | list[str]):
    """
    функция получает комманду для операций создания или изменения узллов сети и параметр и отправляет их на сервер
    запросы разбиваются на чанки размером set_group_step_data
    если при запросе возникла ошибка то вызывается исключение
    """
    # проверяются поддерживаемые команды
    if command in ['host.create', 'host.delete', 'host.update']:
        result = []
        # создаем объект класса работы с сервером
        req = BaseRequest(host=HOST, api_token=API_TOKEN)
        # set_group_step_data - указывается в config файле
        step_data = set_group_step_data
        # делим при необоходимости список заданий на чанки размером step_data
        for i in range(0, len(data), step_data):
            params = request(command, params=data[i : i + step_data])
            hosts = req.post_request_with_token(params)
            if hosts.status is True:
                data_request = json.loads(hosts.data)
                if 'result' in data_request:
                    result = result + data_request['result']['hostids']
                else:
                    raise Exception(f'Измнения не применились: {command}')
            else:
                raise Exception(f'Ошибка: {hosts.error}')
    else:
        raise Exception(f'Не поддерживамая команда: {command}')

    return result


def match_task(data: list[list], set_host: list[str], index_host: list[str]) -> list[list]:
    """
    функция получает пользовательские данные отсортированные по отдельной задаче
    и результаты проведения оперпаций по данной задаче
    и сопоставляет их
    """
    # сравнивеются количество заданий с количеством вернувшихся id
    if len(set_host) == len(index_host):
        # перебираем задания по типу задачи
        for count_host, host in enumerate(set_host):
            # при типе задачи на добавление в задачу добавляем id созданного узла сети
            if data[index_host[count_host]][0] in command_hosts_not_present:
                data[index_host[count_host]].append('')
                data[index_host[count_host]].append('')
                data[index_host[count_host]].append(host)
            if data[index_host[count_host]][0] in command_hosts_present and data[index_host[count_host]][8] != host:
                # при типе задачи на удаление и изменение проверяем совпадения id группы
                # полученной при валидации и полученной от сервер
                raise Exception('Номер группы в data не равен в cgroup')
    else:
        raise Exception('Добавлены(изменены) не все элеементы, set_host не равно index_host')

    return data
