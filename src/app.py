# import json

# from jsonrpcclient import request

# from config import API_TOKEN, HOST
# from http_base.request_base import BaseRequest
# from zabbix.grops_handler import handler_grop
from zabbix.hosts_handler import handler_hosts


def main():
    # handler_grop()
    handler_hosts()


if __name__ == '__main__':
    main()
