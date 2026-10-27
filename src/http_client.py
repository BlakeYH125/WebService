from xml.etree import ElementTree

import requests

BASE_URL = "http://127.0.0.1:8888"
NUMBER_FIELDS = {"uid", "timestamp", "profile", "query"}


def make_xml(root_tag, values):
    root = ElementTree.Element(root_tag)
    for key, value in values.items():
        if value is not None:
            field = ElementTree.SubElement(root, key)
            field.text = str(value)
    return ElementTree.tostring(root, encoding="utf-8")


def parse_record(element):
    record = {}
    for child in element:
        value = child.text or ""
        if child.tag in NUMBER_FIELDS:
            value = int(value)
        record[child.tag] = value
    return record


def parse_response(response):
    root = ElementTree.fromstring(response.content)
    if response.status_code == 401:
        raise PermissionError(root.findtext("message"))
    if root.tag == "error":
        raise ValueError(root.findtext("message"))
    collection_tags = {"profiles", "queries", "feedbacks", "report"}
    if root.tag in collection_tags:
        return [parse_record(child) for child in root]
    return parse_record(root)


class HTTPClient:
    def __init__(self, username, password, base_url=BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)

    def request(self, method, path, params=None, xml=None):
        url = self.base_url + path
        headers = {"Content-Type": "application/xml"}
        options = {
            "params": params,
            "data": xml,
            "headers": headers,
            "auth": self.auth,
        }
        response = requests.request(method, url, **options)
        return parse_response(response)

    def put_insert_profile(self, uid):
        path = f"/rest/api/v3/insert-profile/{uid}"
        return self.request("PUT", path)

    def get_dump_profile(self):
        return self.request("GET", "/rest/api/v3/dump-profile")

    def get_retrieve_profile(self, uid):
        params = {"uid": uid}
        return self.request("GET", "/rest/api/v3/retrieve-profile", params)

    def patch_edit_profile(self, uid, timestamp):
        path = f"/rest/api/v3/edit-profile/{uid}"
        body = make_xml("profile", {"timestamp": timestamp})
        return self.request("PATCH", path, xml=body)

    def put_insert_query(self, uid, arg, profile, description=None):
        path = f"/rest/api/v3/insert-query/{uid}"
        params = {"arg": arg, "profile": profile}
        if description is not None:
            params["description"] = description
        return self.request("PUT", path, params)

    def get_dump_query(self, profile):
        path = f"/rest/api/v3/dump-query/{profile}"
        return self.request("GET", path)

    def get_retrieve_query(self, uid):
        params = {"uid": uid}
        return self.request("GET", "/rest/api/v3/retrieve-query", params)

    def patch_edit_query(self, uid, **fields):
        path = f"/rest/api/v3/edit-query/{uid}"
        body = make_xml("query", fields)
        return self.request("PATCH", path, xml=body)

    def get_dump_feedback(self, query):
        path = f"/rest/api/v3/dump-feedback/{query}"
        return self.request("GET", path)

    def get_retrieve_feedback(self, uid):
        params = {"uid": uid}
        return self.request("GET", "/rest/api/v3/retrieve-feedback", params)

    def get_dump_report(self):
        return self.request("GET", "/rest/api/v3/dump-report")