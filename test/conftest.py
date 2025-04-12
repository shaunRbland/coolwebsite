"""
Pytest fixtures to overload the database functions and ensure
we are in an independet testing database

This allow us to overload the database functions,
meaning our db is self contained for the testing sessions.

Pretty much boilerplate from https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#client-fixture

conftest.py is some pytest dependency injection magic.
"""

import logging

import pytest

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from webapp.main import app

from webapp.database import get_session

# And our utilites
from test import utils

# Remove the somwhat irritating message on __about__ from passlib
logging.getLogger("passlib").setLevel(logging.ERROR)
# Reduce log level of https to remove noise
logging.getLogger("httpx").setLevel(logging.ERROR)


@pytest.fixture(name="session")
def session_fixture():
    """
    Overload the get_session dependency to give us
    an independent testing database.

    The Database is in memory to avoid writing to disk
    """

    engine = create_engine(
        "sqlite://", echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        utils.create_db(session)
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Fixture to setup the web client.

    This creates the session override etc,
    and allows us to use the testing db
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
