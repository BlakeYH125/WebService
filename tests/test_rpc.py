import socket
import time
from threading import Thread

from hypothesis import settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)

from src import data_access_layer as data
from src import rpc_server
from src.rpc_client import RPCClient

TEXT = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=8,
)
STATUS = st.sampled_from(["new", "done", "error"])


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]


TEST_PORT = get_free_port()
rpc_server.PORT = TEST_PORT
rpc_server.print = lambda *args, **kwargs: None
SERVER_THREAD = Thread(target=rpc_server.serve_forever, daemon=True)
SERVER_THREAD.start()
time.sleep(0.1)


class RPCStateMachine(RuleBasedStateMachine):
    @initialize()
    def initialize_model(self):
        data.profiles.clear()
        data.queries.clear()
        data.feedbacks.clear()
        self.client = RPCClient(port=TEST_PORT)
        self.profiles = []
        self.queries = []
        self.feedbacks = []
        self.create_initial_profile()
        self.create_initial_query()
        self.create_initial_feedback()

    def create_initial_profile(self):
        profile = self.client.create_profile()
        self.profiles.append(profile.copy())
        assert self.client.get_profiles() == self.profiles
        assert self.client.get_profile(profile["uid"]) == profile
        profile = self.client.update_profile(
            profile["uid"], 1750000000
        )
        self.profiles[0] = profile.copy()

    def create_initial_query(self):
        query = self.client.create_query(
            "python", self.profiles[0]["uid"], "test", "new"
        )
        self.queries.append(query.copy())
        assert self.client.get_queries() == self.queries
        assert self.client.get_query(query["uid"]) == query
        query = self.client.update_query(
            query["uid"], description="updated", status="done"
        )
        self.queries[0] = query.copy()

    def create_initial_feedback(self):
        feedback = self.client.create_feedback(
            "result", "error", "TimeoutError", self.queries[0]["uid"]
        )
        self.feedbacks.append(feedback.copy())
        assert self.client.get_feedbacks() == self.feedbacks
        assert self.client.get_feedback(feedback["uid"]) == feedback
        feedback = self.client.update_feedback(
            feedback["uid"],
            response="fixed",
            status="done",
            exception="None",
        )
        self.feedbacks[0] = feedback.copy()
        assert self.client.get_recent_exceptions() == (
            self.expected_recent_exceptions()
        )

    def expected_recent_exceptions(self):
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

    @rule()
    def create_profile(self):
        profile = self.client.create_profile()
        self.profiles.append(profile.copy())

    @rule(timestamp=st.integers(min_value=1, max_value=2000000000))
    def update_profile(self, timestamp):
        profile = self.client.update_profile(
            self.profiles[0]["uid"], timestamp
        )
        self.profiles[0] = profile.copy()

    @rule(arg=TEXT, description=TEXT, status=STATUS)
    def create_query(self, arg, description, status):
        query = self.client.create_query(
            arg,
            self.profiles[0]["uid"],
            description,
            status,
        )
        self.queries.append(query.copy())

    @rule(arg=TEXT, description=TEXT, status=STATUS)
    def update_query(self, arg, description, status):
        query = self.client.update_query(
            self.queries[0]["uid"],
            arg=arg,
            description=description,
            status=status,
        )
        self.queries[0] = query.copy()

    @rule(response=TEXT, status=STATUS, exception=TEXT)
    def create_feedback(self, response, status, exception):
        feedback = self.client.create_feedback(
            response,
            status,
            exception,
            self.queries[0]["uid"],
        )
        self.feedbacks.append(feedback.copy())

    @rule(response=TEXT, status=STATUS, exception=TEXT)
    def update_feedback(self, response, status, exception):
        feedback = self.client.update_feedback(
            self.feedbacks[0]["uid"],
            response=response,
            status=status,
            exception=exception,
        )
        self.feedbacks[0] = feedback.copy()

    @rule(uid=st.integers(min_value=1000, max_value=2000))
    def get_missing_profile(self, uid):
        try:
            self.client.get_profile(uid)
        except ValueError as error:
            assert str(error) == "Профиль не найден"
        else:
            message = (
                "Ожидалась ошибка для "
                "отсутствующего профиля"
            )
            raise AssertionError(message)

    @invariant()
    def rpc_state_matches_model(self):
        assert self.client.get_profiles() == self.profiles
        assert self.client.get_queries() == self.queries
        assert self.client.get_feedbacks() == self.feedbacks
        for profile in self.profiles:
            received = self.client.get_profile(profile["uid"])
            assert received == profile
        for query in self.queries:
            received = self.client.get_query(query["uid"])
            assert received == query
        for feedback in self.feedbacks:
            received = self.client.get_feedback(feedback["uid"])
            assert received == feedback
        assert self.client.get_recent_exceptions() == (
            self.expected_recent_exceptions()
        )


TestRPCStateMachine = RPCStateMachine.TestCase
TestRPCStateMachine.settings = settings(
    max_examples=10,
    stateful_step_count=15,
    deadline=None,
)