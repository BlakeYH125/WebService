import time

profiles = []
queries = []
feedbacks = []


def get_next_uid(table):
    if len(table) == 0:
        return 1
    return max(record["uid"] for record in table) + 1


def create_profile():
    profile = {
        "uid": get_next_uid(profiles),
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


def create_query(arg, profile, description, status):
    get_profile(profile)

    query = {
        "uid": get_next_uid(queries),
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


def update_query(uid, arg=None, profile=None, description=None,
                 status=None):
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


def create_feedback(response, status, exception, query):
    get_query(query)

    feedback = {
        "uid": get_next_uid(feedbacks),
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


def handle_create_profile():
    print(create_profile())


def handle_get_profiles():
    print(get_profiles())


def handle_get_profile(uid):
    print(get_profile(int(uid)))


def handle_create_query(arg, profile, description, status):
    print(create_query(arg, int(profile), description, status))


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


def handle_create_feedback(response, status, exception, query):
    print(create_feedback(response, status, exception, int(query)))


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
