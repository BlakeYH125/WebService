# WebService

## 1. Общее описание

Проект представляет собой прототип слоя доступа к данным веб-приложения.

На текущем этапе реализовано хранение данных в оперативной памяти без использования базы данных и без сохранения данных на диск.

Данные представлены тремя списками:

- `profiles` — профили;
- `queries` — запросы;
- `feedbacks` — результаты обработки запросов.

Каждая запись в списке представлена словарём Python.

Связи между сущностями:

```text
Profile -> Query -> Feedback
```

`Query.profile` содержит идентификатор записи `Profile`, а `Feedback.query` содержит идентификатор записи `Query`.

Структура проекта:

```text
WebService/
├── src/
│   └── data_access_layer.py
└── .gitignore
```

Для работы требуется Python 3.10 или новее.

---

## 2. Функции

### Вспомогательные функции

#### `get_next_uid(table)`

Возвращает следующий свободный идентификатор `uid` для указанного списка записей.

#### `parse_fields(parts, allowed_fields)`

Обрабатывает параметры редактирования, переданные через REPL в формате:

```text
поле=значение
```

Также проверяет, разрешено ли изменять указанное поле.

---

### Profile

Структура записи:

```python
{
    "uid": 1,
    "timestamp": 1750000000,
}
```

#### `create_profile()`

Создаёт новый профиль.

`uid` и `timestamp` устанавливаются автоматически.

#### `get_profiles()`

Возвращает список всех профилей.

#### `get_profile(uid)`

Возвращает профиль по его идентификатору.

Если профиль не найден, возникает ошибка:

```text
Профиль не найден
```
---

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

#### `create_query(arg, profile, description, status)`

Создаёт новый запрос.

При создании проверяется существование указанного профиля.

#### `get_queries()`

Возвращает список всех запросов.

#### `get_query(uid)`

Возвращает запрос по его идентификатору.

Если запрос не найден, возникает ошибка:

```text
Запрос не найден
```

#### `update_query(uid, arg=None, profile=None, description=None, status=None)`

Редактирует запрос.

Изменяются только переданные параметры:

- `arg`;
- `profile`;
- `description`;
- `status`.

При изменении `profile` проверяется существование нового профиля.

---

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

#### `create_feedback(response, status, exception, query)`

Создаёт новую запись обратной связи.

При создании проверяется существование указанного запроса.

#### `get_feedbacks()`

Возвращает список всех записей обратной связи.

#### `get_feedback(uid)`

Возвращает запись по её идентификатору.

Если запись не найдена, возникает ошибка:

```text
Обратная связь не найдена
```

#### `update_feedback(uid, response=None, status=None, exception=None, query=None)`

Редактирует запись.

Изменяются только переданные параметры:

- `response`;
- `status`;
- `exception`;
- `query`.

При изменении `query` проверяется существование нового запроса.

---

### `get_recent_exceptions()`

Выполняет соединение данных `Profile`, `Query` и `Feedback`.

В результат попадают записи `Feedback`, созданные не более 6 минут назад.

Для каждой найденной записи возвращаются:

- `exception` из `Feedback`;
- `description` из `Query`.

Пример результата:

```python
[
    {
        "exception": "TimeoutError",
        "description": "test",
    }
]
```

---

### `repl()`

Запускает интерактивный режим работы со слоем доступа к данным.

Поддерживаемые команды:

```text
create_profile
get_profiles
get_profile <uid>

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

---

## 3. Сборка и запуск

Проект не требует отдельной сборки и не использует сторонние зависимости.

Клонирование репозитория:

```bash
git clone https://github.com/BlakeYH125/WebService.git
cd WebService
```

Запуск:

```bash
python src/data_access_layer.py
```

или:

```bash
python3 src/data_access_layer.py
```

После запуска открывается REPL:

```text
>
```

Автоматические тесты на текущем этапе проекта не реализованы.

---

## 4. Примеры использования

### Создание профиля

```text
> create_profile
{'uid': 1, 'timestamp': 1750000000}
```

### Получение всех профилей

```text
> get_profiles
[{'uid': 1, 'timestamp': 1750000000}]
```

### Получение профиля

```text
> get_profile 1
{'uid': 1, 'timestamp': 1750000000}
```

### Создание запроса

```text
> create_query python 1 test new
{'uid': 1, 'timestamp': 1750000200, 'arg': 'python', 'profile': 1, 'description': 'test', 'status': 'new'}
```

### Частичное изменение запроса

```text
> update_query 1 status=done
{'uid': 1, 'timestamp': 1750000200, 'arg': 'python', 'profile': 1, 'description': 'test', 'status': 'done'}
```

Можно изменить несколько полей:

```text
> update_query 1 description=new_description status=processed
```

### Создание Feedback

```text
> create_feedback response error TimeoutError 1
{'uid': 1, 'timestamp': 1750000300, 'response': 'response', 'status': 'error', 'exception': 'TimeoutError', 'query': 1}
```

### Изменение Feedback

```text
> update_feedback 1 status=processed
```

### Выборка записей за последние 6 минут

```text
> recent
[{'exception': 'TimeoutError', 'description': 'new_description'}]
```

### Обработка ошибки

```text
> get_profile 100
Ошибка: Профиль не найден
```

```text
> get_query 100
Ошибка: Запрос не найден
```

### Завершение работы

```text
> exit
```
