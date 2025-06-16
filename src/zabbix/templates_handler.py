import json

from jsonrpcclient import request

from config import API_TOKEN, HOST
from data_class.data_zabbix import GetParamZabbixModel
from http_base.request_base import BaseRequest


def get_templates(data: GetParamZabbixModel) -> dict:
    """
    функция получает параметр для запроса шаблонов на сервер и возвращает результат в фрмате словаря,
    если при запросе возникла ошибка то вызывается исключение
    """
    # из класса с заданием формируется словарь с исключением полей раыных None
    params = data.model_dump(exclude_none=True)
    # формируется jrps запрос
    params = request('template.get', params=params)
    # создается класс для обращения по http и отпарвялется запрос
    req = BaseRequest(host=HOST, api_token=API_TOKEN)
    templates = req.post_request_with_token(params)
    if templates.status is True:
        result = json.loads(templates.data)
    else:
        # если запрос вернулся с ошибколй в части http то вызывается исключение
        raise Exception(f'Ошибка: {templates.error}')

    return result
