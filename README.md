# WebService

Веб-приложение с HTTP API для асинхронного преобразования файлов из формата JPEG в формат PNG.

## Структура проекта

```text
WebService/
├── examples/
│   ├── example_1.jpeg
│   ├── example_2.jpeg
│   ├── example_3.jpeg
│   └── run_examples.sh
├── src/
│   ├── data_access_layer.py
│   ├── demo_http.py
│   ├── http_client.py
│   ├── http_server.py
│   ├── jpeg_to_png.py
│   ├── rpc_client.py
│   └── rpc_server.py
├── tests/
│   ├── http/
│   │   └── test_http_api.py
│   └── rpc/
│       └── test_rpc.py
├── .coveragerc
├── requirements.txt
├── run.sh
└── README.md
```

## Установка зависимостей

Из корня проекта выполните:

```bash
python -m pip install -r requirements.txt
```

## Преобразование JPEG в PNG

Файл `src/jpeg_to_png.py` получает JPEG через стандартный поток ввода и записывает PNG в стандартный поток вывода.

Для запуска примеров выполните:

```bash
bash examples/run_examples.sh
```

PNG-файлы будут созданы в папке `examples`.

## Слой доступа к данным

Файл `src/data_access_layer.py` хранит профили, запросы и результаты обработки в оперативной памяти.

Слой данных выполняет следующие действия:

- создаёт записи с явно указанным положительным UID;
- проверяет, что UID ещё не занят;
- получает и редактирует записи;
- проверяет существование связанных записей;
- формирует отчёт по результатам обработки за последние шесть минут.

## HTTP API

Сервер работает по адресу:

```text
http://127.0.0.1:8888
```

Данные для авторизации:

```text
Логин: student
Пароль: student
```

Доступные методы:

| Метод | Адрес | Назначение |
| --- | --- | --- |
| PUT | `/rest/api/v3/insert-profile/<uid>` | Создание профиля |
| GET | `/rest/api/v3/dump-profile` | Получение всех профилей |
| GET | `/rest/api/v3/retrieve-profile?uid=<uid>` | Получение профиля |
| PATCH | `/rest/api/v3/edit-profile/<uid>` | Редактирование профиля |
| PUT | `/rest/api/v3/insert-query/<uid>` | Создание запроса |
| GET | `/rest/api/v3/dump-query/<profile>` | Получение запросов профиля |
| GET | `/rest/api/v3/retrieve-query?uid=<uid>` | Получение запроса |
| PATCH | `/rest/api/v3/edit-query/<uid>` | Редактирование запроса |
| GET | `/rest/api/v3/dump-feedback/<query>` | Получение результатов запроса |
| GET | `/rest/api/v3/retrieve-feedback?uid=<uid>` | Получение результата |
| GET | `/rest/api/v3/dump-report` | Получение отчёта |

При создании запроса передаются параметры:

- `arg` – абсолютный путь к JPEG-файлу;
- `profile` – UID существующего профиля;
- `description` – необязательное описание.

Новый запрос получает статус `NEW`. Преобразование выполняется в отдельном потоке. После обработки статус меняется на `DONE` или `ERROR`.

Результат обработки получает такой же UID, как соответствующий запрос. При успешном преобразовании поле `response` содержит абсолютный путь к созданному PNG-файлу.

## Запуск сервера

Из корня проекта выполните:

```bash
bash run.sh student student
```

Сервер будет доступен по адресу:

```text
http://127.0.0.1:8888
```

Для остановки сервера нажмите `Ctrl+C`.

## Проверка через HTTP-клиент

Файл `src/demo_http.py` запускает сервер и открывает интерактивную консоль с переменными `client` и `jpeg_path`.

Запуск:

```bash
python -m src.demo_http
```

Команды для проверки:

```python
client.put_insert_profile(1)
client.get_dump_profile()
client.get_retrieve_profile(1)
client.patch_edit_profile(1, 1760000000)
client.put_insert_query(1, str(jpeg_path), 1)
client.get_dump_query(1)
client.get_retrieve_query(1)
client.patch_edit_query(1, description="Изменённое описание")
```

```python
client.get_dump_feedback(1)
client.get_retrieve_feedback(1)
client.get_dump_report()
```

Чтобы использовать другой JPEG-файл, передайте его путь при запуске:

```bash
python -m src.demo_http /absolute/path/image.jpeg
```

## Тестирование HTTP API

Запуск HTTP-тестов:

```bash
python -m unittest discover -s tests/http -v
```

Проверка покрытия:

```bash
python -m coverage erase
python -m coverage run -m unittest discover -s tests/http
python -m coverage report -m
```