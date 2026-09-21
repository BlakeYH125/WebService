# WebService

## 1. Общее описание

Проект представляет собой прототип веб-приложения для варианта 29.
Данные хранятся в оперативной памяти и не сохраняются на диск.

В проекте реализованы:

- модель слоя доступа к данным;
- удалённый вызов процедур на основе TCP;
- RPC-клиент для вызова функций модели;
- тестирование RPC на основе модели с использованием Hypothesis;
- формирование отчёта о покрытии ветвей с использованием Coverage.

Данные представлены тремя списками:

- `profiles` — профили;
- `queries` — запросы;
- `feedbacks` — результаты обработки запросов.

Каждая запись представлена словарём Python. Связи между сущностями:

```text
Profile -> Query -> Feedback
```

Поле `Query.profile` содержит идентификатор `Profile`, а поле
`Feedback.query` содержит идентификатор `Query`.

## 2. Структура проекта

```text
WebService/
├── src/
│   ├── __init__.py
│   ├── data_access_layer.py
│   ├── demo_rpc.py
│   ├── rpc_client.py
│   └── rpc_server.py
├── tests/
│   └── test_rpc.py
├── .coveragerc
├── .gitignore
└── README.md
```

Для работы требуется Python 3.10 или новее.

## 3. Модель слоя доступа к данным

Модель находится в файле `src/data_access_layer.py`. Данные хранятся в
списках `profiles`, `queries` и `feedbacks`.

### Profile

Структура записи:

```python
{
    "uid": 1,
    "timestamp": 1750000000,
}
```

Поддерживаемые функции:

- `create_profile()`;
- `get_profiles()`;
- `get_profile(uid)`;
- `update_profile(uid, timestamp=None)`.

Поле `uid` создаётся автоматически и не редактируется. Функция
`update_profile` изменяет поле `timestamp`.

### Query

Структура записи:

```python
{
    "uid": 1,
    "timestamp": 1750000000,
    "arg": "python",
    "profile": 1,
    "description": "test",
    "status": "new",
}
```

Поддерживаемые функции:

- `create_query(arg, profile, description, status)`;
- `get_queries()`;
- `get_query(uid)`;
- `update_query(uid, arg=None, profile=None, description=None, status=None)`.

При создании запроса и изменении поля `profile` проверяется существование
соответствующего профиля.

### Feedback

Структура записи:

```python
{
    "uid": 1,
    "timestamp": 1750000000,
    "response": "result",
    "status": "done",
    "exception": "None",
    "query": 1,
}
```

Поддерживаемые функции:

- `create_feedback(response, status, exception, query)`;
- `get_feedbacks()`;
- `get_feedback(uid)`;
- `update_feedback(uid, response=None, status=None, exception=None,
  query=None)`.

При создании записи и изменении поля `query` проверяется существование
соответствующего запроса.

### Соединение данных

Функция `get_recent_exceptions()` соединяет данные `Profile`, `Query` и
`Feedback`. В результат включаются записи `Feedback`, созданные не более
шести минут назад.

Результат содержит поля:

- `exception` из `Feedback`;
- `description` из `Query`.

Всего модель содержит 13 основных функций: по четыре функции для каждой из
трёх сущностей и одну функцию соединения данных.

## 4. REPL

Для запуска интерактивного режима выполните:

```bash
python3 src/data_access_layer.py
```

Поддерживаемые команды:

```text
create_profile
get_profiles
get_profile <uid>
update_profile <uid> <timestamp>

create_query <arg> <profile> <description> <status>
get_queries
get_query <uid>
update_query <uid> [arg=...] [profile=...] [description=...] [status=...]

create_feedback <response> <status> <exception> <query>
get_feedbacks
get_feedback <uid>
update_feedback <uid> [response=...] [status=...] [exception=...] [query=...]

recent
exit
```

## 5. RPC на основе TCP

RPC-сервер находится в `src/rpc_server.py`, а клиент — в
`src/rpc_client.py`.

Сервер принимает запрос, определяет функцию по коду операции, вызывает её в
модели слоя данных и возвращает результат клиенту. Тела запросов и ответов
передаются в формате JSON. Используется порядок байт от старшего к младшему.

### Структура запроса

| Поле | Размер |
| --- | ---: |
| Размер тела запроса | 3 байта |
| Код операции | 2 байта |
| Тело в формате JSON | Определяется запросом |

### Структура ответа

| Поле | Размер |
| --- | ---: |
| Версия протокола | 1 байт |
| Код операции | 2 байта |
| Размер тела ответа | 5 байт |
| Тело в формате JSON | Определяется ответом |

Коды операций:

| Код | Метод |
| ---: | --- |
| 1 | `create_profile` |
| 2 | `get_profiles` |
| 3 | `get_profile` |
| 4 | `update_profile` |
| 5 | `create_query` |
| 6 | `get_queries` |
| 7 | `get_query` |
| 8 | `update_query` |
| 9 | `create_feedback` |
| 10 | `get_feedbacks` |
| 11 | `get_feedback` |
| 12 | `update_feedback` |
| 13 | `get_recent_exceptions` |

Все полученные RPC-запросы журналируются в стандартный вывод сервера.

### Запуск сервера

Из корня проекта выполните:

```bash
python3 -m src.rpc_server
```

По умолчанию сервер запускается по адресу `127.0.0.1:5000`.

### Демонстрация клиента

Не останавливая сервер, откройте второй терминал и выполните:

```bash
python3 src/demo_rpc.py
```

Файл `demo_rpc.py` последовательно вызывает все 13 методов RPC-клиента.

## 6. Тестирование на основе модели

Тест находится в файле `tests/test_rpc.py` и использует класс
`RuleBasedStateMachine` из библиотеки Hypothesis.

Во время тестирования используются два состояния:

- настоящее состояние, которое хранится на RPC-сервере;
- упрощённая модель из списков `profiles`, `queries` и `feedbacks`.

Hypothesis генерирует последовательности создания и редактирования записей.
После каждого действия инвариант получает данные через RPC и сравнивает их с
упрощённой моделью. В тесте вызываются все 13 методов RPC-клиента.

### Установка библиотек

Активируйте виртуальное окружение и установите зависимости:

```bash
python -m pip install hypothesis coverage
```

### Запуск тестирования

```bash
python -m coverage erase
python -m coverage run -m unittest discover -s tests
python -m coverage report -m
```
