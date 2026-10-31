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
RECENT_PERIOD_SECONDS = 6 * 60


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
    profiles = stateful.Bundle("profiles")
    queries = stateful.Bundle("queries")

    @stateful.initialize()
    def initialize(self):
        data.profiles.clear()
        data.queries.clear()
        data.feedbacks.clear()
        self.client = HTTPClient(USERNAME, PASSWORD, BASE_URL)

    @staticmethod
    def find_by_uid(records, uid):
        return next(record for record in records if record["uid"] == uid)

    @staticmethod
    def assert_query(query, uid, arg, profile, description, status):
        assert query["uid"] == uid
        assert query["arg"] == arg
        assert query["profile"] == profile
        assert query["description"] == description
        assert query["status"] == status

    @staticmethod
    def assert_timestamp(timestamp, before, after):
        assert isinstance(timestamp, int)
        assert before <= timestamp <= after

    def get_all_queries(self):
        queries = []

        for profile in self.client.get_dump_profile():
            queries.extend(self.client.get_dump_query(profile["uid"]))

        return queries

    def get_next_profile_uid(self):
        profiles = self.client.get_dump_profile()
        return max([0] + [profile["uid"] for profile in profiles]) + 1

    def get_next_query_uid(self):
        queries = self.get_all_queries()
        return max([0] + [query["uid"] for query in queries]) + 1

    @stateful.rule(target=profiles)
    def insert_profile(self):
        uid = self.get_next_profile_uid()
        before = int(time.time())
        received = self.client.put_insert_profile(uid)
        after = int(time.time())

        assert set(received) == {"uid", "timestamp"}
        assert received["uid"] == uid
        self.assert_timestamp(received["timestamp"], before, after)

        profiles = self.client.get_dump_profile()
        inserted = next(profile for profile in profiles if
                        profile["uid"] == uid)

        assert inserted == received

        return received["uid"]

    @stateful.rule(profile_uid=profiles)
    def dump_profile(self, profile_uid):
        profiles = self.client.get_dump_profile()

        assert isinstance(profiles, list)
        assert any(profile["uid"] == profile_uid for profile in profiles)

        for profile in profiles:
            assert set(profile) == {"uid", "timestamp"}

    @stateful.rule(profile_uid=profiles)
    def retrieve_profile(self, profile_uid):
        profiles = self.client.get_dump_profile()
        profile = next(profile for profile in profiles if
                       profile["uid"] == profile_uid)
        received = self.client.get_retrieve_profile(profile_uid)

        assert received == profile

    @stateful.rule(profile_uid=profiles, timestamp=TIMESTAMP)
    def edit_profile(self, profile_uid, timestamp):
        received = self.client.patch_edit_profile(profile_uid, timestamp)

        assert received["uid"] == profile_uid
        assert received["timestamp"] == timestamp
        assert self.client.get_retrieve_profile(profile_uid) == received

    @stateful.rule(target=queries,
                   profile_uid=profiles,
                   arg=ARGUMENT,
                   description=TEXT)
    def insert_query(self, profile_uid, arg, description):
        uid = self.get_next_query_uid()
        before = int(time.time())
        profile = profile_uid
        created = self.client.put_insert_query(uid, arg,
                                               profile, description)
        after = int(time.time())

        self.assert_query(created, uid, arg,
                          profile, description, NEW_STATUS)
        self.assert_timestamp(created["timestamp"], before, after)

        queries = self.client.get_dump_query(profile)
        inserted = self.find_by_uid(queries, uid)

        self.assert_query(inserted, uid, arg,
                          profile, description, DONE_STATUS)

        return created["uid"]

    @stateful.rule(profile_uid=profiles)
    def dump_query(self, profile_uid):
        queries = self.client.get_dump_query(profile_uid)

        assert isinstance(queries, list)

        for query in queries:
            assert query["profile"] == profile_uid

    @stateful.rule(query_uid=queries)
    def retrieve_query(self, query_uid):
        queries = self.get_all_queries()
        query = next(query for query in queries if query["uid"] == query_uid)
        received = self.client.get_retrieve_query(query_uid)

        assert received == query

    @stateful.rule(query_uid=queries,
                   profile_uid=profiles,
                   arg=ARGUMENT,
                   description=TEXT,
                   status=STATUS)
    def edit_query(self, query_uid, profile_uid, arg, description, status):
        received = self.client.patch_edit_query(
            query_uid,
            arg=arg,
            profile=profile_uid,
            description=description,
            status=status)

        assert received["uid"] == query_uid
        assert received["arg"] == arg
        assert received["profile"] == profile_uid
        assert received["description"] == description
        assert received["status"] == status
        assert self.client.get_retrieve_query(query_uid) == received

    @stateful.rule(query_uid=queries)
    def dump_feedback(self, query_uid):
        feedbacks = self.client.get_dump_feedback(query_uid)

        assert isinstance(feedbacks, list)
        assert len(feedbacks) > 0

        for feedback in feedbacks:
            assert feedback["query"] == query_uid

    @stateful.rule(query_uid=queries)
    def retrieve_feedback(self, query_uid):
        feedbacks = self.client.get_dump_feedback(query_uid)

        assert len(feedbacks) > 0

        feedback_uid = feedbacks[0]["uid"]
        received = self.client.get_retrieve_feedback(feedback_uid)

        assert received == feedbacks[0]

    @stateful.rule(query_uid=queries)
    def dump_report(self, query_uid):
        received = self.client.get_dump_report()

        assert isinstance(received, list)

        query = self.client.get_retrieve_query(query_uid)
        feedbacks = self.client.get_dump_feedback(query_uid)
        recent_feedbacks = [feedback for feedback in feedbacks if
                            feedback["timestamp"] >= int(time.time())
                            - RECENT_PERIOD_SECONDS]

        if recent_feedbacks:
            assert any(entry["description"] ==
                       query["description"] for entry in received)


TestHTTPStateMachine = HTTPStateMachine.TestCase
TestHTTPStateMachine.settings = settings(
    max_examples=10,
    stateful_step_count=15,
    deadline=None)
