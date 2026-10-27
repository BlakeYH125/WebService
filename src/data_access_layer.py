import time

profiles = []
queries = []
feedbacks = []
MIN_UID = 1


def validate_new_uid(uid, table, entity_name):
    if uid < MIN_UID:
        raise ValueError("UID должен быть положительным")
    if any(record["uid"] == uid for record in table):
        raise ValueError(f"{entity_name} с таким UID уже существует")


def create_profile(uid):
    validate_new_uid(uid, profiles, "Профиль")
    profile = {
        "uid": uid,
        "timestamp": int(time.time()),
    }
    profiles.append(profile)
    return profile


def get_profiles():
    return profiles


def get_profile(uid):
    assert uid is not None
    for profile in profiles:
        if profile["uid"] == uid:
            return profile
    raise ValueError("Профиль не найден")


def update_profile(uid, timestamp=None):
    assert uid is not None
    profile = get_profile(uid)
    if timestamp is not None:
        profile["timestamp"] = timestamp
    return profile


def create_query(uid, arg, profile, description, status):
    validate_new_uid(uid, queries, "Запрос")
    get_profile(profile)

    query = {
        "uid": uid,
        "timestamp": int(time.time()),
        "arg": arg,
        "profile": profile,
        "description": description,
        "status": status,
    }
    queries.append(query)
    return query


def get_queries():
    return queries


def get_query(uid):
    assert uid is not None
    for query in queries:
        if query["uid"] == uid:
            return query
    raise ValueError("Запрос не найден")


def update_query(uid, arg=None, profile=None, description=None, status=None):
    assert uid is not None
    query = get_query(uid)

    if arg is not None:
        query["arg"] = arg

    if profile is not None:
        get_profile(profile)
        query["profile"] = profile

    if description is not None:
        query["description"] = description

    if status is not None:
        query["status"] = status

    return query


def create_feedback(uid, response, status, exception, query):
    validate_new_uid(uid, feedbacks, "Результат")
    get_query(query)

    feedback = {
        "uid": uid,
        "timestamp": int(time.time()),
        "response": response,
        "status": status,
        "exception": exception,
        "query": query,
    }
    feedbacks.append(feedback)
    return feedback


def get_feedbacks():
    return feedbacks


def get_feedback(uid):
    assert uid is not None
    for feedback in feedbacks:
        if feedback["uid"] == uid:
            return feedback
    raise ValueError("Обратная связь не найдена")


def update_feedback(uid, response=None, status=None,
                    exception=None, query=None):
    assert uid is not None
    feedback = get_feedback(uid)

    if response is not None:
        feedback["response"] = response

    if status is not None:
        feedback["status"] = status

    if exception is not None:
        feedback["exception"] = exception

    if query is not None:
        get_query(query)
        feedback["query"] = query

    return feedback


def get_recent_exceptions():
    result = []
    now = int(time.time())

    for profile in profiles:
        for query in queries:
            if profile["uid"] == query["profile"]:
                for feedback in feedbacks:
                    query_matches = query["uid"] == feedback["query"]
                    is_recent = feedback["timestamp"] >= now - 360

                    if query_matches and is_recent:
                        result.append({
                            "exception": feedback["exception"],
                            "description": query["description"],
                        })

    return result


def parse_fields(parts, allowed_fields):
    result = {}

    for part in parts:
        if "=" not in part:
            raise ValueError(
                "Параметры редактирования задаются как поле=значение")

        key, value = part.split("=", 1)

        if key not in allowed_fields:
            raise ValueError(f"Неизвестное поле: {key}")

        result[key] = value

    return result


def handle_create_profile(uid):
    print(create_profile(int(uid)))


def handle_get_profiles():
    print(get_profiles())


def handle_get_profile(uid):
    print(get_profile(int(uid)))


def handle_update_profile(uid, timestamp):
    print(update_profile(int(uid), int(timestamp)))


def handle_create_query(uid, arg, profile, description, status):
    print(create_query(int(uid), arg, int(profile), description, status))


def handle_get_queries():
    print(get_queries())


def handle_get_query(uid):
    print(get_query(int(uid)))


def handle_update_query(uid, *fields):
    allowed_fields = {"arg", "profile", "description", "status"}
    data = parse_fields(fields, allowed_fields)
    profile = data.get("profile")

    if profile is not None:
        profile = int(profile)

    arg = data.get("arg")
    description = data.get("description")
    status = data.get("status")
    print(update_query(int(uid), arg, profile, description, status))


def handle_create_feedback(uid, response, status, exception, query):
    uid = int(uid)
    query = int(query)
    print(create_feedback(uid, response, status, exception, query))


def handle_get_feedbacks():
    print(get_feedbacks())


def handle_get_feedback(uid):
    print(get_feedback(int(uid)))


def handle_update_feedback(uid, *fields):
    allowed_fields = {"response", "status", "exception", "query"}
    data = parse_fields(fields, allowed_fields)
    query = data.get("query")

    if query is not None:
        query = int(query)

    response = data.get("response")
    status = data.get("status")
    exception = data.get("exception")
    print(update_feedback(int(uid), response, status, exception, query))


def handle_recent():
    print(get_recent_exceptions())


COMMANDS = {
    "create_profile": handle_create_profile,
    "get_profiles": handle_get_profiles,
    "get_profile": handle_get_profile,
    "update_profile": handle_update_profile,
    "create_query": handle_create_query,
    "get_queries": handle_get_queries,
    "get_query": handle_get_query,
    "update_query": handle_update_query,
    "create_feedback": handle_create_feedback,
    "get_feedbacks": handle_get_feedbacks,
    "get_feedback": handle_get_feedback,
    "update_feedback": handle_update_feedback,
    "recent": handle_recent,
}


def repl():
    while True:
        try:
            parts = input("> ").strip().split()

            if not parts:
                continue

            command = parts[0]

            if command == "exit":
                break

            handler = COMMANDS.get(command)

            if handler is None:
                raise ValueError("Неизвестная команда")

            handler(*parts[1:])

        except ValueError as error:
            print("Ошибка:", error)
        except TypeError:
            print("Ошибка: неверное количество аргументов")


if __name__ == "__main__":
    repl()
