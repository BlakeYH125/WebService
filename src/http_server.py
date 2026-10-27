import argparse
import subprocess
import sys
from pathlib import Path
from threading import Thread
from xml.etree import ElementTree

from flask import Flask, Response, request

from src import data_access_layer as data

HOST = "127.0.0.1"
PORT = 8888
XML_TYPE = "application/xml"
DEFAULT_DESCRIPTION = "JPEG-Image"
NEW_STATUS = "NEW"
DONE_STATUS = "DONE"
ERROR_STATUS = "ERROR"
SUCCESS_CODE = 0

app = Flask(__name__)
app.config["API_USERNAME"] = ""
app.config["API_PASSWORD"] = ""
app.config["TEST_MODE"] = False


def add_record(parent, tag, record):
    element = ElementTree.SubElement(parent, tag)
    for key, value in record.items():
        field = ElementTree.SubElement(element, key)
        field.text = str(value)


def xml_record(tag, record):
    root = ElementTree.Element(tag)
    for key, value in record.items():
        field = ElementTree.SubElement(root, key)
        field.text = str(value)
    body = ElementTree.tostring(root, encoding="utf-8")
    return Response(body, mimetype=XML_TYPE)


def xml_records(root_tag, item_tag, records):
    root = ElementTree.Element(root_tag)
    for record in records:
        add_record(root, item_tag, record)
    body = ElementTree.tostring(root, encoding="utf-8")
    return Response(body, mimetype=XML_TYPE)


def xml_error(message, status=200):
    root = ElementTree.Element("error")
    field = ElementTree.SubElement(root, "message")
    field.text = message
    body = ElementTree.tostring(root, encoding="utf-8")
    return Response(body, status=status, mimetype=XML_TYPE)


def required_argument(name):
    value = request.args.get(name)
    if value is None:
        raise ValueError(f"Отсутствует параметр {name}")
    return value


def read_xml(allowed_fields):
    root = ElementTree.fromstring(request.data)
    values = {}
    for child in root:
        if child.tag not in allowed_fields:
            raise ValueError(f"Неизвестное поле: {child.tag}")
        values[child.tag] = child.text or ""
    return values


def is_authorized():
    auth = request.authorization
    if auth is None:
        return False
    valid_user = auth.username == app.config["API_USERNAME"]
    valid_password = auth.password == app.config["API_PASSWORD"]
    return valid_user and valid_password


@app.before_request
def authorize_request():
    if is_authorized():
        return None
    response = xml_error("Требуется авторизация", 401)
    response.headers["WWW-Authenticate"] = 'Basic realm="WebService"'
    return response


@app.errorhandler(ValueError)
@app.errorhandler(AssertionError)
@app.errorhandler(ElementTree.ParseError)
def handle_request_error(error):
    message = str(error) or "Некорректный запрос"
    return xml_error(message)


def finish_test_task(query_uid):
    data.update_query(query_uid, status=DONE_STATUS)
    data.create_feedback(query_uid, "", DONE_STATUS, "", query_uid)


def execute_task(query_uid):
    query = data.get_query(query_uid)
    try:
        source_path = Path(query["arg"])
        if not source_path.is_absolute():
            raise ValueError("Путь к JPEG должен быть абсолютным")
        if not source_path.is_file():
            raise ValueError("Файл JPEG не найден")
        source = source_path.read_bytes()
        script = Path(__file__).with_name("jpeg_to_png.py")
        command = [sys.executable, str(script)]
        options = {
            "input": source,
            "capture_output": True,
        }
        result = subprocess.run(command, check=False, **options)
        if result.returncode != SUCCESS_CODE:
            message = result.stderr.decode("utf-8").strip()
            raise ValueError(message or "Не удалось преобразовать JPEG")
        result_path = source_path.with_suffix(".png")
        result_path.write_bytes(result.stdout)
        response = str(result_path)
        data.update_query(query_uid, status=DONE_STATUS)
        data.create_feedback(query_uid, response, DONE_STATUS, "", query_uid)
    except (ValueError, OSError) as error:
        data.update_query(query_uid, status=ERROR_STATUS)
        message = str(error)
        data.create_feedback(query_uid, "", ERROR_STATUS, message, query_uid)


def start_task(query_uid):
    if app.config["TEST_MODE"]:
        finish_test_task(query_uid)
        return
    execute_task(query_uid)


def queries_for_profile(profile):
    result = []
    for query in data.get_queries():
        if query["profile"] == profile:
            result.append(query)
    return result


def feedbacks_for_query(query_uid):
    result = []
    for feedback in data.get_feedbacks():
        if feedback["query"] == query_uid:
            result.append(feedback)
    return result


@app.put("/rest/api/v3/insert-profile/<uid>")
def put_insert_profile(uid):
    uid = int(uid)
    profile = data.create_profile(uid)
    return xml_record("profile", profile)


@app.get("/rest/api/v3/dump-profile")
def get_dump_profile():
    return xml_records("profiles", "profile", data.get_profiles())


@app.get("/rest/api/v3/retrieve-profile")
def get_retrieve_profile():
    uid = int(required_argument("uid"))
    return xml_record("profile", data.get_profile(uid))


@app.patch("/rest/api/v3/edit-profile/<uid>")
def patch_edit_profile(uid):
    uid = int(uid)
    values = read_xml({"timestamp"})
    timestamp = values.get("timestamp")
    if timestamp is not None:
        timestamp = int(timestamp)
    profile = data.update_profile(uid, timestamp)
    return xml_record("profile", profile)


@app.put("/rest/api/v3/insert-query/<uid>")
def put_insert_query(uid):
    uid = int(uid)
    arg = required_argument("arg")
    profile = int(required_argument("profile"))
    description = request.args.get("description", DEFAULT_DESCRIPTION)
    query = data.create_query(uid, arg, profile, description, NEW_STATUS)
    response = xml_record("query", query.copy())
    start_task(uid)
    return response


@app.get("/rest/api/v3/dump-query/<profile>")
def get_dump_query(profile):
    profile = int(profile)
    queries = queries_for_profile(profile)
    return xml_records("queries", "query", queries)


@app.get("/rest/api/v3/retrieve-query")
def get_retrieve_query():
    uid = int(required_argument("uid"))
    return xml_record("query", data.get_query(uid))


@app.patch("/rest/api/v3/edit-query/<uid>")
def patch_edit_query(uid):
    uid = int(uid)
    fields = {"arg", "profile", "description", "status"}
    values = read_xml(fields)
    profile = values.get("profile")
    if profile is not None:
        profile = int(profile)
    arg = values.get("arg")
    description = values.get("description")
    status = values.get("status")
    query = data.update_query(uid, arg, profile, description, status)
    return xml_record("query", query)


@app.get("/rest/api/v3/dump-feedback/<query>")
def get_dump_feedback(query):
    query = int(query)
    feedbacks = feedbacks_for_query(query)
    return xml_records("feedbacks", "feedback", feedbacks)


@app.get("/rest/api/v3/retrieve-feedback")
def get_retrieve_feedback():
    uid = int(required_argument("uid"))
    return xml_record("feedback", data.get_feedback(uid))


@app.get("/rest/api/v3/dump-report")
def get_dump_report():
    report = data.get_recent_exceptions()
    return xml_records("report", "entry", report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--test-mode", action="store_true")
    arguments = parser.parse_args()
    app.config["API_USERNAME"] = arguments.username
    app.config["API_PASSWORD"] = arguments.password
    app.config["TEST_MODE"] = arguments.test_mode
    app.run(host=HOST, port=PORT)


if __name__ == "__main__":
    main()