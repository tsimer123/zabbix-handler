# import json

# from jsonrpcclient import request

# from config import API_TOKEN, HOST
# from http_base.request_base import BaseRequest
from zabbix.grops_handler import handler_grop


def main():
    handler_grop()
    # req = BaseRequest(host=HOST, api_token=API_TOKEN)

    # get_host = request('host.get', params={'output': ['hostid', 'host'], 'selectInterfaces': ['interfaceid', 'ip']})

    # poarams_host = {
    #     'host': 'tele_192.168.1.1',
    #     'interfaces': [{'type': 1, 'main': 1, 'useip': 1, 'ip': '192.168.3.1', 'dns': '', 'port': '10050'}],
    #     'groups': [{'groupid': '50'}],
    #     'templates': [{'templateid': '20045'}],
    # }

    # poarams_group = [{'name': 'тест11/тест2'}, {'name': 'тест2/тест1/тест3'}]

    # paran_get_group = {
    #     'output': ['name', 'groupid'],
    #     'search': {'name': '*тест*'},
    #     'searchWildcardsEnabled': True,
    #     'searchByAny': True,
    #     'sortfield': 'groupid',
    # }

    # # 'startSearch': True,

    # create_group = request('hostgroup.create', params=poarams_group)

    # get_group = request('hostgroup.get', params=paran_get_group)

    # get_host = request('hostgroup.create', params=poarams_host)

    # # data = {
    # #     'jsonrpc': '2.0',
    # #     'method': 'host.get',
    # #     'params': {'output': ['hostid', 'host'], 'selectInterfaces': ['interfaceid', 'ip']},
    # #     'id': 2,
    # # }

    # hosts = req.post_request_with_token(get_group)

    # result = json.loads(hosts.data)

    # print(result)


if __name__ == '__main__':
    main()
