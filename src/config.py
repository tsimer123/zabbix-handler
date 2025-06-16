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
set_group_step_data = 2

# разрешенные команды для групп
group_command = [
    'add',
    'del',
    'update',
]

# разрешенные команды для узлов сети
group_command = [
    'add',
    'del',
    'update',
    'active',
    'deactive',
]

# команды для опреций с имеющимся хостами на сервере
command_hosts = [
    'add',
    'del',
    # 'update',
    'active',
    'deactive',
]

# команды для опреций с имеющимся хостами на сервере
command_hosts_present = [
    'del',
    'update',
    'active',
    'deactive',
]

# команды для опреций с отсутвуюзими хостами на сервере
command_hosts_not_present = [
    'add',
]

# команды для опреций с расширенными параметрами
command_extended_parameters = ['add', 'update']

# заголовок для таблицы с результами обработки ГРУПП
header_results_group = [
    'Команда',
    'Параметр 1',
    'Параметр 2',
    'Статус валидации',
    'Ошибка',
    'Резултьтат добавления',
    'id',
]

# заголовок для таблицы с результами обработки УСЛОВ СЕТИ
header_results_host = [
    'Команда',
    'Имя узла сети',
    'IP',
    'ID шаблонов',
    'Группы',
    'Статус валидации',
    'Ошибка',
    'Резултьтат добавления',
    'id',
]
