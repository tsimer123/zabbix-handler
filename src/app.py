import datetime

from argument_start import get_args
from zabbix.get_host_handler import handler_get_hosts
from zabbix.grops_handler import handler_grop
from zabbix.hosts_handler import handler_hosts


def main():
    print(f'{datetime.datetime.now()}: Запуск приложения')
    args = get_args()
    if args['type'] == 'get_host':
        if args['get_host_group'] is not None and args['get_host_items'] is not None:
            handler_get_hosts(args['get_host_items'], args['get_host_group'])
        else:
            print('Не заполнены обязательные аргуременты get_host_items или get_host_group')
    if args['type'] == 'host':
        handler_hosts()
    if args['type'] == 'group':
        handler_grop()

    print(f'{datetime.datetime.now()}: Работа приложения оконочена')


if __name__ == '__main__':
    main()
