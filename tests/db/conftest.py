"""Shared fixtures for the database connection tests."""

import asyncio
import sqlite3

import httpx
import pytest
from datasette.app import Datasette

from moutils.db.datasette import DatasetteConnection

# ---------------------------------------------------------------------------
# PostHog fixtures — frozen DatabaseSchemaQuery / HogQLQuery replies.
# ---------------------------------------------------------------------------


@pytest.fixture
def hogql_result():
    """A representative HogQLQuery response with columns + types + results."""
    return {
        "columns": ["date", "n"],
        "types": [["date", "Date"], ["n", "UInt64"]],
        "results": [
            ["2026-01-01", 5],
            ["2026-01-02", 8],
            ["2026-01-03", 3],
            ["2026-01-04", 1],
            ["2026-01-05", 9],
        ],
    }


@pytest.fixture
def schema_response():
    """A frozen DatabaseSchemaQuery reply covering two tables."""
    return {
        "tables": {
            "events": {
                "name": "events",
                "fields": {
                    "uuid": {"name": "uuid", "type": "string"},
                    "event": {"name": "event", "type": "string"},
                    "timestamp": {"name": "timestamp", "type": "datetime"},
                    "properties": {"name": "properties", "type": "json"},
                },
            },
            "persons": {
                "name": "persons",
                "fields": {
                    "id": {"name": "id", "type": "string"},
                    "created_at": {"name": "created_at", "type": "datetime"},
                },
            },
        }
    }


# ---------------------------------------------------------------------------
# Datasette fixtures — mocked + in-process live.
# ---------------------------------------------------------------------------

# The connector points at a non-localhost host so pytest-httpx intercepts it;
# Datasette's own client stays on localhost (see non_mocked_hosts) and passes
# through to the real ASGI app.
_CONNECTOR_HOST = "http://datasette.test"
_DB_NAME = "sample"


@pytest.fixture
def sample_db(tmp_path):
    """A temp SQLite db with two tables of known data."""
    path = tmp_path / f"{_DB_NAME}.db"
    con = sqlite3.connect(path)
    con.executescript(
        """
        create table dogs (id integer primary key, name text, age integer);
        insert into dogs (name, age) values ('Cleo', 5), ('Pancakes', 3);
        create table cats (id integer primary key, nickname text);
        insert into cats (nickname) values ('Mr Whiskers');
        """
    )
    con.commit()
    con.close()
    return path


@pytest.fixture
def ds(sample_db):
    return Datasette([str(sample_db)])


@pytest.fixture
def non_mocked_hosts():
    # Let Datasette's internal ds.client (localhost) reach the real ASGI app.
    return ["localhost"]


@pytest.fixture
def live_conn(httpx_mock, ds):
    """A DatasetteConnection whose httpx calls hit the in-process Datasette."""
    loop = asyncio.new_event_loop()

    def route(request: httpx.Request) -> httpx.Response:
        async def run():
            resp = await ds.client.request(
                request.method,
                request.url.raw_path.decode("ascii"),  # path + query string
            )
            return httpx.Response(
                status_code=resp.status_code,
                headers=resp.headers,
                content=resp.content,
            )

        return loop.run_until_complete(run())

    httpx_mock.add_callback(route, is_reusable=True)
    conn = DatasetteConnection(_CONNECTOR_HOST, _DB_NAME)
    try:
        yield conn
    finally:
        conn.close()
        loop.close()


_LIVE_TOKEN = "s3cret-test-token"


@pytest.fixture
def live_token():
    return _LIVE_TOKEN


@pytest.fixture
def ds_authed(sample_db):
    """In-process Datasette locked down with datasette-auth-tokens.

    Anonymous requests are denied (`allow: {id: "*"}` requires an authenticated
    actor). The test token authenticates as actor ``demo``.
    """
    return Datasette(
        [str(sample_db)],
        metadata={
            "allow": {"id": "*"},
            "plugins": {
                "datasette-auth-tokens": {
                    "tokens": [{"token": _LIVE_TOKEN, "actor": {"id": "demo"}}]
                }
            },
        },
    )


@pytest.fixture
def route_authed(httpx_mock, ds_authed):
    """Route connector calls into the authed instance, forwarding the token."""
    loop = asyncio.new_event_loop()

    def route(request: httpx.Request) -> httpx.Response:
        async def run():
            headers = {}
            if "authorization" in request.headers:
                headers["authorization"] = request.headers["authorization"]
            resp = await ds_authed.client.request(
                request.method,
                request.url.raw_path.decode("ascii"),
                headers=headers,
            )
            return httpx.Response(
                status_code=resp.status_code,
                headers=resp.headers,
                content=resp.content,
            )

        return loop.run_until_complete(run())

    httpx_mock.add_callback(route, is_reusable=True)
    try:
        yield
    finally:
        loop.close()
