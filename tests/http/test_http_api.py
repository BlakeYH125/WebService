import logging
import socket
import time
from threading import Thread

from hypothesis import settings, stateful
from hypothesis import strategies as st
from werkzeug.serving import make_server

from src import data_access_layer as data
from src.http_client import HTTPClient
from src.http_server import app

USERNAME = "student"
PASSWORD = "student"
TEXT = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)
ARGUMENT = TEXT.map(lambda name: f"/tmp/{name}.jpeg")
STATUS = st.sampled_from(["NEW", "DONE", "ERROR"])
TIMESTAMP = st.integers(min_value=1, max_value=2000000000)
DEFAULT_DESCRIPTION = "JPEG-Image"
NEW_STATUS = "NEW"
DONE_STATUS = "DONE"


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


TEST_PORT = get_free_port()
BASE_URL = "http://127.0.0.1:" + str(TEST_PORT)
logging.getLogger("werkzeug").disabled = True
app.config["API_USERNAME"] = USERNAME
app.config["API_PASSWORD"] = PASSWORD
app.config["TEST_MODE"] = True
SERVER = make_server("127.0.0.1", TEST_PORT, app)
SERVER_THREAD = Thread(target=SERVER.serve_forever, daemon=True)
SERVER_THREAD.start()


class HTTPStateMachine(stateful.RuleBasedStateMachine):
    @stateful.initialize()
    def initialize_model(self):
        data.profiles.clear()
        data.queries.clear()
        data.feedbacks.clear()
        self.client = HTTPClient(USERNAME, PASSWORD, BASE_URL)
        self.profiles = []
        self.queries = []
        self.feedbacks = []

    @staticmethod
    def assert_timestamp(timestamp, before, after):
        assert isinstance(timestamp, int)
        assert before <= timestamp <= after

    def create_profile_and_check(self, uid):
        before = int(time.time())
        received = self.client.put_insert_profile(uid)
        after = int(time.time())
        self.assert_timestamp(received["timestamp"], before, after)
        expected = {"uid": uid, "timestamp": received["timestamp"]}
        assert received == expected
        self.profiles.append(expected)

    def edit_profile_and_check(self, uid, timestamp):
        received = self.client.patch_edit_profile(uid, timestamp)
        current = next(profile for profile in self.profiles if profile["uid"] == uid)
        expected = current.copy()
        expected["timestamp"] = timestamp
        assert received == expected
        current.update(expected)

    def create_query_and_check(self, uid, arg, profile, description=None):
        before = int(time.time())
        created = self.client.put_insert_query(uid, arg, profile, description)
        after = int(time.time())
        self.assert_timestamp(created["timestamp"], before, after)
        expected_description = DEFAULT_DESCRIPTION if description is None else description
        expected_created = {
            "uid": uid,
            "timestamp": created["timestamp"],
            "arg": arg,
            "profile": profile,
            "description": expected_description,
            "status": NEW_STATUS,
        }
        assert created == expected_created
        received_query = self.client.get_retrieve_query(uid)
        expected_query = expected_created.copy()
        expected_query["status"] = DONE_STATUS
        assert received_query == expected_query
        received_feedback = self.client.get_retrieve_feedback(uid)
        self.assert_timestamp(received_feedback["timestamp"], before, after)
        expected_feedback = {
            "uid": uid,
            "timestamp": received_feedback["timestamp"],
            "response": "",
            "status": DONE_STATUS,
            "exception": "",
            "query": uid,
        }
        assert received_feedback == expected_feedback
        self.queries.append(expected_query)
        self.feedbacks.append(expected_feedback)

    def edit_query_description_and_check(self, uid, description):
        received = self.client.patch_edit_query(uid, description=description)
        current = next(query for query in self.queries if query["uid"] == uid)
        expected = current.copy()
        expected["description"] = description
        assert received == expected
        current.update(expected)

    def edit_all_query_fields_and_check(self, uid, arg, profile, description, status):
        received = self.client.patch_edit_query(uid, arg=arg, profile=profile, description=description, status=status)
        current = next(query for query in self.queries if query["uid"] == uid)
        expected = current.copy()
        expected["arg"] = arg
        expected["profile"] = profile
        expected["description"] = description
        expected["status"] = status
        assert received == expected
        current.update(expected)

    def expected_report(self):
        result = []
        for profile in self.profiles:
            for query in self.queries:
                if profile["uid"] == query["profile"]:
                    for feedback in self.feedbacks:
                        if query["uid"] == feedback["query"]:
                            result.append({
                                "exception": feedback["exception"],
                                "description": query["description"],
                            })
        return result

    def assert_server_matches_model(self):
        assert self.client.get_dump_profile() == self.profiles
        for profile in self.profiles:
            uid = profile["uid"]
            assert self.client.get_retrieve_profile(uid) == profile
            expected_queries = [query for query in self.queries if query["profile"] == uid]
            assert self.client.get_dump_query(uid) == expected_queries
        for query in self.queries:
            uid = query["uid"]
            assert self.client.get_retrieve_query(uid) == query
            expected_feedbacks = [feedback for feedback in self.feedbacks if feedback["query"] == uid]
            assert self.client.get_dump_feedback(uid) == expected_feedbacks
        for feedback in self.feedbacks:
            assert self.client.get_retrieve_feedback(feedback["uid"]) == feedback
        assert self.client.get_dump_report() == self.expected_report()

    @stateful.rule()
    def create_profile(self):
        uid = max([0] + [profile["uid"] for profile in self.profiles]) + 1
        self.create_profile_and_check(uid)

    @stateful.rule(timestamp=TIMESTAMP)
    def edit_profile(self, timestamp):
        self.edit_profile_and_check(self.profiles[0]["uid"], timestamp)

    @stateful.rule(arg=ARGUMENT, description=TEXT)
    def create_query(self, arg, description):
        uid = max([0]+[query["uid"] for query in self.queries]) + 1
        profile = self.profiles[uid % len(self.profiles)]["uid"]
        self.create_query_and_check(uid, arg, profile, description)

    @stateful.rule(description=TEXT)
    def edit_query_description(self, description):
        self.edit_query_description_and_check(self.queries[0]["uid"], description)

    @stateful.rule(arg=ARGUMENT, description=TEXT, status=STATUS)
    def edit_all_query_fields(self, arg, description, status):
        query = self.queries[0]
        first_profile = self.profiles[0]["uid"]
        second_profile = self.profiles[1]["uid"]
        profile = second_profile if query["profile"] == first_profile else first_profile
        self.edit_all_query_fields_and_check(query["uid"], arg, profile, description, status)

    @stateful.invariant()
    def server_state_matches_model(self):
        self.assert_server_matches_model()


TestHTTPStateMachine = HTTPStateMachine.TestCase
TestHTTPStateMachine.settings = settings(max_examples=10, stateful_step_count=15, deadline=None)
