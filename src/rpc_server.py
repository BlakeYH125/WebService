import json
import socket
from src import data_access_layer as data

HOST = "127.0.0.1"
PORT = 5000
PROTOCOL_VERSION = 1

FUNCTIONS = {
    1: data.create_profile,
    2: data.get_profiles,
    3: data.get_profile,
    4: data.update_profile,
    5: data.create_query,
    6: data.get_queries,
    7: data.get_query,
    8: data.update_query,
    9: data.create_feedback,
    10: data.get_feedbacks,
    11: data.get_feedback,
    12: data.update_feedback,
    13: data.get_recent_exceptions,
}


def receive_exact(connection, size):
    result = b""
    while len(result) < size:
        part = connection.recv(size - len(result))
        if not part:
            raise ConnectionError("Соединение закрыто")
        result += part
    return result


def handle_request(connection):
    header = receive_exact(connection, 5)
    body_size = int.from_bytes(header[:3], "big")
    operation_code = int.from_bytes(header[3:5], "big")
    request = json.loads(receive_exact(connection, body_size).decode("utf-8"))
    print(f"RPC request: operation={operation_code}, body={request}")

    try:
        function = FUNCTIONS.get(operation_code)
        if function is None:
            raise ValueError("Неизвестный код операции")
        result = function(*request.get("args", []))
        response = {"result": result}
    except (AssertionError, TypeError, ValueError) as error:
        response = {"error": str(error) or "Некорректные аргументы"}

    body = json.dumps(response, ensure_ascii=False).encode("utf-8")
    response_header = (PROTOCOL_VERSION.to_bytes(1, "big") +
                       operation_code.to_bytes(2, "big")
                       + len(body).to_bytes(5, "big"))
    connection.sendall(response_header + body)


def serve_forever():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"RPC server started on {HOST}:{PORT}")

        while True:
            connection, _ = server.accept()

            with connection:
                try:
                    handle_request(connection)
                except (ConnectionError, json.JSONDecodeError,
                        UnicodeDecodeError, OverflowError) as error:
                    print(f"RPC request error: {error}")


if __name__ == "__main__":
    serve_forever()