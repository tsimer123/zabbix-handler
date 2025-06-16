import ipaddress
import re

from zabbix.data_static import slovar

# def get_entities(data: GetParamZabbixModel, type_req: str, name_key) -> dict:
#     """
#     функция получает параметр для запроса на сервер и возвращает результат в фрмате словаря,
#     если при запросе возникла ошибка то вызывается исключение
#     """

#     result = []
#     # создаем объект класса работы с сервером
#     req = BaseRequest(host=HOST, api_token=API_TOKEN)
#     # set_group_step_data - указывается в config файле
#     step_data = set_group_step_data
#     # делим при необоходимости список заданий на чанки размером step_data
#     for i in range(0, len(data), step_data):
#         params = request(data, params=data[i : i + step_data])

#     # из класса с заданием формируется словарь с исключением полей раыных None
#     params = data.model_dump(exclude_none=True)
#     # формируется jrps запрос
#     params = request('hostgroup.get', params=params)
#     # создается класс для обращения по http и отпарвялется запрос
#     req = BaseRequest(host=HOST, api_token=API_TOKEN)
#     groups = req.post_request_with_token(params)
#     if groups.status is True:
#         result = json.loads(groups.data)
#     else:
#         # если запрос вернулся с ошибколй в части http то вызывается исключение
#         raise Exception(f'Ошибка: {groups.error}')

#     return result


def transliterate_host(name: str) -> str:
    """
    функция траслитизациия из кирилицы в латиницу
    """
    if name is not None:
        name = name.lower()

        if re.fullmatch(r'[a-z0-9а-я\_.\-\/]+', name) is not None:
            # Циклически заменяем все буквы в строке
            for key in slovar:
                name = name.replace(key, slovar[key])
            return name
        else:
            raise Exception('имя хоста не валидное, разрешенные символы: a-z, 0-9, а-я, ., -, /')
    else:
        raise Exception('name = None')


def is_valid_ipv4(ip_str):
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        return False
