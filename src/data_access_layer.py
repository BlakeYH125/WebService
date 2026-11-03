import os
import time
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import orm

MIN_UID = 1
RECENT_PERIOD_SECONDS = 6 * 60
DEFAULT_DATABASE_FILE = (
        Path(__file__).resolve().parent.parent / "webservice.db")
DATABASE_ENVIRONMENT_VARIABLE = "WEBSERVICE_DATABASE_FILE"
DATABASE_NAME = os.getenv(DATABASE_ENVIRONMENT_VARIABLE)
DATABASE_FILE = Path(DATABASE_NAME) \
    if DATABASE_NAME else DEFAULT_DATABASE_FILE
DATABASE_URL = "sqlite:///" + str(DATABASE_FILE)
CONNECTION_OPTIONS = {"check_same_thread": False}
ENGINE = sa.create_engine(DATABASE_URL, connect_args=CONNECTION_OPTIONS)
SessionFactory = orm.sessionmaker(bind=ENGINE)
PROFILE_NOT_FOUND = "Профиль не найден"
QUERY_NOT_FOUND = "Запрос не найден"
FEEDBACK_NOT_FOUND = "Обратная связь не найдена"


class Base(orm.DeclarativeBase):
    pass


class ProfileRecord(Base):
    __tablename__ = "profiles"

    uid: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    timestamp: orm.Mapped[int] = orm.mapped_column(sa.Integer,
                                                   nullable=False)


class QueryRecord(Base):
    __tablename__ = "queries"

    uid: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    timestamp: orm.Mapped[int] = orm.mapped_column(sa.Integer,
                                                   nullable=False)
    arg: orm.Mapped[str] = orm.mapped_column(sa.String, nullable=False)
    profile: orm.Mapped[int] = (
        orm.mapped_column(sa.ForeignKey("profiles.uid")))
    description: orm.Mapped[str] = orm.mapped_column(sa.String,
                                                     nullable=False)
    status: orm.Mapped[str] = orm.mapped_column(sa.String,
                                                nullable=False)


class FeedbackRecord(Base):
    __tablename__ = "feedbacks"

    uid: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    timestamp: orm.Mapped[int] = orm.mapped_column(sa.Integer,
                                                   nullable=False)
    response: orm.Mapped[str] = orm.mapped_column(sa.String,
                                                  nullable=False)
    status: orm.Mapped[str] = orm.mapped_column(sa.String,
                                                nullable=False)
    exception: orm.Mapped[str] = orm.mapped_column(sa.String,
                                                   nullable=False)
    query: orm.Mapped[int] = (
        orm.mapped_column(sa.ForeignKey("queries.uid")))


Base.metadata.create_all(ENGINE)


def profile_to_dict(profile):
    return {"uid": profile.uid, "timestamp": profile.timestamp}


def query_to_dict(query):
    return {
        "uid": query.uid,
        "timestamp": query.timestamp,
        "arg": query.arg,
        "profile": query.profile,
        "description": query.description,
        "status": query.status,
    }


def feedback_to_dict(feedback):
    return {
        "uid": feedback.uid,
        "timestamp": feedback.timestamp,
        "response": feedback.response,
        "status": feedback.status,
        "exception": feedback.exception,
        "query": feedback.query,
    }


def validate_new_uid(session, model, uid, entity_name):
    if uid < MIN_UID:
        raise ValueError("UID должен быть положительным")
    if session.get(model, uid) is not None:
        message = f"{entity_name} с таким UID уже существует"
        raise ValueError(message)


def require_record(session, model, uid, message):
    record = session.get(model, uid)
    if record is None:
        raise ValueError(message)
    return record


def create_profile(uid):
    with SessionFactory.begin() as session:
        validate_new_uid(session, ProfileRecord, uid, "Профиль")
        profile = ProfileRecord(uid=uid, timestamp=int(time.time()))
        session.add(profile)
        session.flush()
        return profile_to_dict(profile)


def get_profiles():
    with SessionFactory() as session:
        statement = sa.select(ProfileRecord).order_by(ProfileRecord.uid)
        profiles = session.scalars(statement).all()
        return [profile_to_dict(profile) for profile in profiles]


def get_profile(uid):
    assert uid is not None
    with SessionFactory() as session:
        profile = require_record(session,
                                 ProfileRecord,
                                 uid,
                                 PROFILE_NOT_FOUND)
        return profile_to_dict(profile)


def update_profile(uid, timestamp=None):
    assert uid is not None
    with SessionFactory.begin() as session:
        profile = require_record(session,
                                 ProfileRecord,
                                 uid,
                                 PROFILE_NOT_FOUND)
        if timestamp is not None:
            profile.timestamp = timestamp
        session.flush()
        return profile_to_dict(profile)


def create_query(uid, arg, profile, description, status):
    with SessionFactory.begin() as session:
        validate_new_uid(session, QueryRecord, uid, "Запрос")
        require_record(session, ProfileRecord, profile, PROFILE_NOT_FOUND)
        values = {
            "uid": uid,
            "timestamp": int(time.time()),
            "arg": arg,
            "profile": profile,
            "description": description,
            "status": status,
        }
        query = QueryRecord(**values)
        session.add(query)
        session.flush()
        return query_to_dict(query)


def get_queries():
    with SessionFactory() as session:
        statement = sa.select(QueryRecord).order_by(QueryRecord.uid)
        queries = session.scalars(statement).all()
        return [query_to_dict(query) for query in queries]


def get_query(uid):
    assert uid is not None
    with SessionFactory() as session:
        query = require_record(session, QueryRecord, uid, QUERY_NOT_FOUND)
        return query_to_dict(query)


def update_query(uid, arg=None, profile=None, description=None, status=None):
    assert uid is not None
    with SessionFactory.begin() as session:
        query = require_record(session, QueryRecord, uid, QUERY_NOT_FOUND)
        if arg is not None:
            query.arg = arg
        if profile is not None:
            require_record(session, ProfileRecord, profile,
                           PROFILE_NOT_FOUND)
            query.profile = profile
        if description is not None:
            query.description = description
        if status is not None:
            query.status = status
        session.flush()
        return query_to_dict(query)


def create_feedback(uid, response, status, exception, query):
    with SessionFactory.begin() as session:
        validate_new_uid(session, FeedbackRecord, uid, "Результат")
        require_record(session, QueryRecord, query, QUERY_NOT_FOUND)
        values = {
            "uid": uid,
            "timestamp": int(time.time()),
            "response": response,
            "status": status,
            "exception": exception,
            "query": query,
        }
        feedback = FeedbackRecord(**values)
        session.add(feedback)
        session.flush()
        return feedback_to_dict(feedback)


def get_feedbacks():
    with SessionFactory() as session:
        statement = sa.select(FeedbackRecord).order_by(FeedbackRecord.uid)
        feedbacks = session.scalars(statement).all()
        return [feedback_to_dict(feedback) for feedback in feedbacks]


def get_feedback(uid):
    assert uid is not None
    with SessionFactory() as session:
        message = FEEDBACK_NOT_FOUND
        feedback = require_record(session, FeedbackRecord, uid, message)
        return feedback_to_dict(feedback)


def update_feedback(uid, response, status, exception, query):
    assert uid is not None
    with SessionFactory.begin() as session:
        message = FEEDBACK_NOT_FOUND
        feedback = require_record(session, FeedbackRecord, uid, message)
        if response is not None:
            feedback.response = response
        if status is not None:
            feedback.status = status
        if exception is not None:
            feedback.exception = exception
        if query is not None:
            require_record(session, QueryRecord, query, QUERY_NOT_FOUND)
            feedback.query = query
        session.flush()
        return feedback_to_dict(feedback)


def get_recent_exceptions():
    threshold = int(time.time()) - RECENT_PERIOD_SECONDS
    with SessionFactory() as session:
        statement = sa.select(
            FeedbackRecord.exception,
            QueryRecord.description,
        )
        statement = statement.join(
            QueryRecord,
            QueryRecord.uid == FeedbackRecord.query,
        )
        statement = statement.join(
            ProfileRecord,
            ProfileRecord.uid == QueryRecord.profile,
        )
        statement = statement.where(FeedbackRecord.timestamp >= threshold)
        rows = session.execute(statement).all()
        return [
            {
                "exception": row.exception,
                "description": row.description,
            }
            for row in rows
        ]


def reset_database():
    with SessionFactory.begin() as session:
        session.execute(sa.delete(FeedbackRecord))
        session.execute(sa.delete(QueryRecord))
        session.execute(sa.delete(ProfileRecord))
