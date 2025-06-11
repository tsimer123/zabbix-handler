import json
import re
from bisect import bisect_left

from jsonrpcclient import request

from config import API_TOKEN, HOST, grop_file, group_command, header_results_group, root_group, set_group_step_data
from data_class.data_zabbix import GetParamZabbixModel
from excel import f_save_xlsx, open_excel
from http_base.request_base import BaseRequest


def handler_grop():
    """функция обрабатывает входной файл с заданием на создание, обновление, удаление групп"""

    # открывается excel файл
    data = open_excel(grop_file)
    if data is not None:
        if len(data) > 1:
            # создается параметр для запроса всех групп на сервере распложенных в корневой группе
            grop_request = GetParamZabbixModel(
                output=['groupid', 'name'],
                search={'name': root_group},
                sortfield='groupid',
                startSearch=True,
                selectHosts='count',
            )
            try:
                # запрашиваются группы с сервера
                group_server = get_grops(grop_request)
                # если ответ корректный
                if 'result' in group_server:
                    # валидиуруются входные данные и сравниваются с данными с сервера
                    data, state_error = valid_group(data[1:], group_server['result'])
                    # проверяется наличие ошибок валидации
                    if state_error is False:
                        # при остутствии ошибок валидации обрабатываются задания и проверяется их выполнеие
                        data = handler_group_params(data)
                        data = post_valid_result(data)
                        # результат сохраняется в excel файле
                        f_save_xlsx('GROUPS_HANDLER', 'results', header_results_group, data)
                    else:
                        # при наличии ошибок валидации формуруется отчет в excel файле
                        f_save_xlsx('GROUPS_HANDLER', 'results', header_results_group, data)

                elif 'error' in group_server:
                    raise Exception(f'ошибка group_server: {group_server["error"]}')
                else:
                    raise Exception(f'не известный результат работы handler_grop.get_grops, result: {group_server}')
            except Exception as ex:
                print(ex)
        else:
            print('Ошибка - файл с заданием пустой')


def get_grops(data: GetParamZabbixModel) -> dict:
    """
    функция получает параметр для запроса групп на сервер и возвращает результат в фрмате словаря,
    если при запросе возникла ошибка то вызывается исключение
    """
    # из класса с заданием формируется словарь с исключением полей раыных None
    params = data.model_dump(exclude_none=True)
    # формируется jrps запрос
    params = request('hostgroup.get', params=params)
    # создается класс для обращения по http и отпарвялется запрос
    req = BaseRequest(host=HOST, api_token=API_TOKEN)
    groups = req.post_request_with_token(params)
    if groups.status is True:
        result = json.loads(groups.data)
    else:
        # если запрос вернулся с ошибколй в части http то вызывается исключение
        raise Exception(f'Ошибка: {groups.error}')

    return result


def set_group(command: str, data: list[dict] | list[str]):
    """
    функция получает комманду для операций создания или изменения групп и параметр и отправляет из на сервер
    завпросы разбиваются на чанки размером set_group_step_data
    если при запросе возникла ошибка то вызывается исключение
    """
    # проверяются поддерживаемые команды
    if command in ['hostgroup.create', 'hostgroup.delete', 'hostgroup.update']:
        result = []
        # создаем объект класса работы с сервером
        req = BaseRequest(host=HOST, api_token=API_TOKEN)
        # set_group_step_data - указывается в config файле
        step_data = set_group_step_data
        # делим при необоходимости список заданий на чанки размером step_data
        for i in range(0, len(data), step_data):
            params = request(command, params=data[i : i + step_data])
            groups = req.post_request_with_token(params)
            if groups.status is True:
                data_request = json.loads(groups.data)
                if 'result' in data_request:
                    result = result + data_request['result']['groupids']
                else:
                    raise Exception(f'Измнения не применились: {command}')
            else:
                raise Exception(f'Ошибка: {groups.error}')
    else:
        raise Exception(f'Не поддерживамая команда: {command}')

    return result


def valid_group(data: list[list], zabbix_req: list[dict]) -> tuple[list[list], bool]:
    """
    функция проверяет вводные данные от пользователя на:
    начичие дублей в параметрых команд
    на пустые значения где это не допустимо
    на конфиликт имен с уже существующиеми группами
    наличие добавляемых/обновляемых или отсутствие удаляемых групп на сервере
    """
    # получаем список всех имен групп из задания (Параметр 1 и Параметр 2)
    param_1 = [line[1] for line in data if line[1] is not None]
    param_2 = [line[2] for line in data if line[2] is not None]
    params_summ = param_1 + param_2
    # удаляем дубли имен групп из задания
    set_params = set(params_summ)
    # сравниваем количество имен групп из задания и количество уникальных имен групп
    # при не совпадении вызывыется исключение с ошибкой
    if len(params_summ) == len(set_params):
        # удаляется из имени группы корневая группа
        for count_l, _ in enumerate(zabbix_req):
            zabbix_req[count_l]['name'] = zabbix_req[count_l]['name'].split('/', 1)[1]

        # переменную отвечающую за наличие в задании ошибок валидации выставляем в False - ошибок нет
        state_error = False
        for count_gr_in, group_in in enumerate(data):
            # проверям имена групп на наличие запрещенных знаков,
            # разрешено латиница и кирилица в вернем и нижнем регистре, числа, - и /
            # и проверятся Параметр 1 на пустое значение None
            if (group_in[1] is not None and re.fullmatch(r'[a-zA-Z0-9а-яА-Я\-\/]+', group_in[1]) is not None) and (
                group_in[2] is None
                or (group_in[2] is not None and re.fullmatch(r'[a-zA-Z0-9а-яА-Я\-\/]+', group_in[2]) is not None)
            ):
                # проверяется тип задания на разрешенный
                if group_in[0] in group_command:
                    trigger_zb_group = 0
                    # перебираются группы присутствующие на сервере
                    for zb_group in zabbix_req:
                        if group_in[1] == zb_group['name']:
                            if group_in[0] == 'add':
                                # если задача на добавлении группы и на сервере есть группа с таким именем
                                # то указывается ошибка
                                trigger_zb_group = 1
                                # статус валидации
                                data[count_gr_in].append(False)
                                # ошибка
                                data[count_gr_in].append(f'Группа с именем: {group_in[1]} присутсвует на сервере')
                                # резултьтат добавления
                                data[count_gr_in].append('Отмена')
                                # признак ошибки устанавивается в True - есть ошибки в задании
                                state_error = True
                                break
                            if group_in[0] == 'del':
                                trigger_zb_group = 1
                                if zb_group['hosts'] == '0':
                                    data[count_gr_in].append(True)
                                    data[count_gr_in].append('')
                                    data[count_gr_in].append('')
                                    # id группы
                                    data[count_gr_in].append(zb_group['groupid'])
                                    break
                                else:
                                    # если в группе на удаление есть узлы сети, такую группу удалить нельзя
                                    data[count_gr_in].append(False)
                                    data[count_gr_in].append(
                                        f'Группу нельзя удалить в ней {zb_group["hosts"]} улов сети'
                                    )
                                    data[count_gr_in].append('Отмена')
                                    state_error = True
                            if group_in[0] == 'update':
                                trigger_zb_group = 1
                                if group_in[2] is not None:
                                    # если Параметр 2 не пустой
                                    # создается список с именами групп равные имени из Параметра 2
                                    trigger_update = [zab_gr for zab_gr in zabbix_req if zab_gr['name'] == group_in[2]]
                                    # проверяется длина списка на личие имени группы из Параметра 2 на сервере
                                    if len(trigger_update) == 0:
                                        # если список пустой можно делать переименование группы
                                        data[count_gr_in].append(True)
                                        data[count_gr_in].append('')
                                        data[count_gr_in].append('')
                                        data[count_gr_in].append(zb_group['groupid'])
                                    else:
                                        # если список не пустой - ошибка
                                        data[count_gr_in].append(False)
                                        data[count_gr_in].append(
                                            f'На сервере присутвует группа с именем: {group_in[2]}'
                                        )
                                        data[count_gr_in].append('Отмена')
                                        state_error = True
                                else:
                                    # если Параметр 2 не пустой - ошибка
                                    data[count_gr_in].append(False)
                                    data[count_gr_in].append('Параметр 2 не может быть пустным')
                                    data[count_gr_in].append('Отмена')
                                    state_error = True
                                break
                    if trigger_zb_group == 0:
                        # если в ответе сервера не найдено имя группы из задания
                        if group_in[0] == 'add':
                            # если операция добавления то можно добавлять
                            data[count_gr_in].append(True)
                        if group_in[0] == 'del':
                            # нечего удалять пишется ошибка
                            data[count_gr_in].append(False)
                            data[count_gr_in].append(f'Группы с именем: {group_in[1]} нет на сервере, нечего удалять')
                            data[count_gr_in].append('Отмена')
                            state_error = True
                        if group_in[0] == 'update':
                            # нечего обновлять пишется ошибка
                            data[count_gr_in].append(False)
                            data[count_gr_in].append(f'Группы с именем: {group_in[1]} нет на сервере, нечего обновлять')
                            data[count_gr_in].append('Отмена')
                            state_error = True

                else:
                    # команда отсутствует в списке разрешенных
                    data[count_gr_in].append(False)
                    data[count_gr_in].append(f'Не валидная команда: {group_in[0]}')
                    data[count_gr_in].append('Отмена')
                    state_error = True
            else:
                # имена групп не валидны
                data[count_gr_in].append(False)
                data[count_gr_in].append(
                    'Имя группы может содержать: a-z, A-Z, 0-9, а-я, А-Я, -, /, также Параметр 1 не должен быть пустым'
                )
                data[count_gr_in].append('Отмена')
                state_error = True

    else:
        # дубли имен групп в задании
        for count_gr_in, _ in enumerate(data):
            data[count_gr_in].append(False)
            data[count_gr_in].append('Обнаружены дубли в столбцах "Параметр 1" и "Параметр 2" по всему документу')
            data[count_gr_in].append('Отмена')
        state_error = True

    return data, state_error


def handler_group_params(data: list[list]) -> list[list]:
    """
    функция сортирует данные от пользвателя по задачаем add, del, update
    отправялет отсортированные данные в функцию для проведения оперций с группами на сервере
    и отправляет данные в функцию для сопоставления данных полученные от пользователя с данными от сервера
    """
    create_group_params = []
    delete_group_params = []
    update_group_params = []

    create_index = []
    delete_index = []
    update_index = []

    # сотируются данные по типам задач
    for index_t, task in enumerate(data):
        if task[0] == 'add':
            # создаем список с заданиями по типу задачи для отправки на сервер
            create_group_params.append({'name': root_group + task[1]})
            # создаем список индексов в общем списке по каждой оперции
            create_index.append(index_t)
        if task[0] == 'del':
            delete_group_params.append(task[6])
            delete_index.append(index_t)
        if task[0] == 'update':
            update_group_params.append({'groupid': task[6], 'name': root_group + task[2]})
            update_index.append(index_t)

    if len(create_group_params) > 0:
        # отправляем отстортированные задачи далее для проведжения опрераций на сервере
        create_group = set_group('hostgroup.create', create_group_params)
        # сопоставляем полученные данные от сервера с входными данными
        data = match_task(data, create_group, create_index)

    if len(delete_group_params) > 0:
        delete_group = set_group('hostgroup.delete', delete_group_params)
        data = match_task(data, delete_group, delete_index)

    if len(update_group_params) > 0:
        update_group = set_group('hostgroup.update', update_group_params)
        data = match_task(data, update_group, update_index)

    return data


def match_task(data: list[list], set_group: list[str], index_group: list[str]) -> list[list]:
    """
    функция получает пользовательские данные отсортированные по отдельной задаче
    и результаты проведения оперпаций по данной задаче
    и сопоставляет их
    """
    # сравнивеются количество заданий с количеством вернувшихся id
    if len(set_group) == len(index_group):
        # перебираем задания по типу задачи
        for count_cgroup, cgroup in enumerate(set_group):
            # при типе задачи на добавление в задачу добавляем id созданной группы
            if data[index_group[count_cgroup]][0] == 'add':
                data[index_group[count_cgroup]].append('')
                data[index_group[count_cgroup]].append('')
                data[index_group[count_cgroup]].append(cgroup)
            if data[index_group[count_cgroup]][0] in ['del', 'update'] and data[index_group[count_cgroup]][6] != cgroup:
                # при типе задачи на удаление и изменение проверяем совпадения id группы
                # полученной при валидации и полученной от сервер
                raise Exception('Номер группы в data не равен в cgroup')
    else:
        raise Exception('Добавлены(изменены) не все элеементы, set_group не равно index_group')

    return data


def post_valid_result(data: list[list]) -> list[list]:
    """
    функция проводит валидацию данных после проведения оперций на сервере с ними
    """
    # создается список из id групп из задания
    groupids = [line[6] for line in data]
    # создается параметр для запроса групп по id и отправляется
    grop_request = GetParamZabbixModel(output=['groupid', 'name'], filter={'groupid': groupids}, sortfield='groupid')
    group_server = get_grops(grop_request)
    if 'result' in group_server:
        # если ответ от сервера положительный
        # создается список с id групп для индексации групп полученных с сервера
        index_group = [line['groupid'] for line in group_server['result']]
        # удаляется из имени группы корневая группа
        for count_gs, _ in enumerate(group_server['result']):
            group_server['result'][count_gs]['name'] = group_server['result'][count_gs]['name'].split('/', 1)[1]
        for count_t, task in enumerate(data):
            # поиск бинарным поиском в индексе ответа сервера по id группы из задания
            index = bisect_left(index_group, task[6])
            if index != len(index_group) and index_group[index] == task[6]:
                if data[count_t][0] == 'add':
                    # если имя группы из задания сходится с именем в ответе от сервера
                    if data[count_t][1] == group_server['result'][index]['name']:
                        # записываем в задание сообщение об успешном выполнении
                        data[count_t][5] = 'Добавлено'
                    else:
                        data[count_t][5] = 'Ошибка'

                if data[count_t][0] == 'update':
                    if data[count_t][2] == group_server['result'][index]['name']:
                        data[count_t][5] = 'Обновлено'
                    else:
                        data[count_t][5] = 'Ошибка'

                if data[count_t][0] == 'del' and data[count_t][2] == group_server['result'][index]['name']:
                    # если найдена группа в ответе серера с командой на удаление, то ошибка
                    data[count_t][5] = 'Ошибка'
            else:
                # если индекс искомой группы больше длины списка (не найден элепмент) с id групп
                # или группа из списка id групп не равна группе из задания
                if data[count_t][0] == 'del':
                    # если команда на удаление првоеряем имя группы из задания и ответа от сервера
                    if data[count_t][1] != group_server['result'][index]['name']:
                        # если имена групп не совпали то записываем успешное выполенние задачи
                        data[count_t][5] = 'Удалено'
                    else:
                        data[count_t][5] = 'Ошибка'

                if data[count_t][0] in ['add', 'update']:
                    # если задание на добавление группы или изменение то записываем ошибку выполнения задачи
                    data[count_t][5] = 'Ошибка'

    elif 'error' in group_server:
        # ошибка сформированная zabbix
        raise Exception(f'ошибка group_server: {group_server["error"]}')
    else:
        raise Exception(f'не известный результат работы post_valid_result.get_grops, result: {group_server}')

    return data
