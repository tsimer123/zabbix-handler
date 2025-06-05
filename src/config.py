import os

from dotenv import load_dotenv

load_dotenv()

# настройки подключения
HOST = os.environ.get('HOST')
API_TOKEN = os.environ.get('API_TOKEN')


# файлы загрузки
grop_file = 'grops.xlsx'
hosts_file = 'hosts.xlsx'
items_file = 'items.xlsx'

# настройки окружения в zabbix
root_group = 'sims/'

# количество элементов в одном запросе при работе с группами
set_group_step_data = 250

# разрешенные команды для групп
group_command = [
    'add',
    'del',
    'update',
]

# заголовок для таблицы с резщультами
header_results_group = [
    'Команда',
    'Параметр 1',
    'Параметр 2',
    'Статус валидации',
    'Ошибка',
    'Резултьтат добавления',
    'id',
]
