import json
import socket

HOST = "127.0.0.1"
PORT = 5000
PROTOCOL_VERSION = 1

OPERATION_CODES = {
    "create_profile": 1,
    "get_profiles": 2,
    "get_profile": 3,
    "update_profile": 4,
    "create_query": 5,
    "get_queries": 6,
    "get_query": 7,
    "update_query": 8,
    "create_feedback": 9,
    "get_feedbacks": 10,
    "get_feedback": 11,
    "update_feedback": 12,
    "get_recent_exceptions": 13,
}


def receive_exact(connection, size):
    result = b""
    while len(result) < size:
        part = connection.recv(size - len(result))
        if not part:
            raise ConnectionError("Соединение закрыто")
        result += part
    return result


class RPCClient:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port

    def call(self, method, *args):
        operation_code = OPERATION_CODES[method]
        body = json.dumps({"args": args}, ensure_ascii=False).encode("utf-8")
        header = (len(body).to_bytes(3, "big")
                  + operation_code.to_bytes(2, "big"))

        with socket.create_connection((self.host, self.port)) as connection:
            connection.sendall(header + body)
            response_header = receive_exact(connection, 8)
            version = response_header[0]
            response_code = int.from_bytes(response_header[1:3], "big")
            response_size = int.from_bytes(response_header[3:8], "big")
            response = json.loads(
                receive_exact(connection, response_size).decode("utf-8"))

        if version != PROTOCOL_VERSION:
            raise ValueError("Неподдерживаемая версия протокола")
        if response_code != operation_code:
            raise ValueError("Код операции в ответе не совпадает с запросом")
        if "error" in response:
            raise ValueError(response["error"])
        return response["result"]

    def create_profile(self):
        return self.call("create_profile")

    def get_profiles(self):
        return self.call("get_profiles")

    def get_profile(self, uid):
        return self.call("get_profile", uid)

    def update_profile(self, uid, timestamp=None):
        return self.call("update_profile", uid, timestamp)

    def create_query(self, arg, profile, description, status):
        return self.call("create_query", arg, profile, description, status)

    def get_queries(self):
        return self.call("get_queries")

    def get_query(self, uid):
        return self.call("get_query", uid)

    def update_query(self, uid, arg=None, profile=None,
                     description=None, status=None):
        return self.call("update_query", uid,
                         arg, profile, description, status)

    def create_feedback(self, response, status, exception, query):
        return self.call("create_feedback", response,
                         status, exception, query)

    def get_feedbacks(self):
        return self.call("get_feedbacks")

    def get_feedback(self, uid):
        return self.call("get_feedback", uid)

    def update_feedback(self, uid, response=None, status=None,
                        exception=None, query=None):
        return self.call("update_feedback", uid, response,
                         status, exception, query)

    def get_recent_exceptions(self):
        return self.call("get_recent_exceptions")