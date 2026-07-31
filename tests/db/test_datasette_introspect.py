"""Tests for Datasette database discovery."""

import pytest

from moutils.db.datasette import DatasetteConnection, databases

_DBS = [
    {"name": "earthquakes", "route": "earthquakes", "is_memory": False},
    {"name": "everest", "route": "everest", "is_memory": False},
    {"name": "_memory", "route": "_memory", "is_memory": True},  # skipped
]


def test_databases_lists_routes_and_skips_memory(httpx_mock):
    httpx_mock.add_response(json=_DBS)
    assert databases("http://ds.test/") == ["earthquakes", "everest"]
    assert str(httpx_mock.get_requests()[0].url) == "http://ds.test/-/databases.json"


def test_databases_accepts_datasette_1_envelope(httpx_mock):
    httpx_mock.add_response(json={"ok": True, "databases": _DBS})
    assert databases("http://ds.test") == ["earthquakes", "everest"]


def test_databases_rejects_bad_shape(httpx_mock):
    httpx_mock.add_response(json={"ok": True})
    with pytest.raises(ValueError, match="databases response shape"):
        databases("http://ds.test")


def test_databases_sends_token(httpx_mock):
    httpx_mock.add_response(json=_DBS)
    databases("http://ds.test", token="sekret")
    assert httpx_mock.get_requests()[0].headers["Authorization"] == "Bearer sekret"


def test_connection_discovers_siblings(httpx_mock):
    # Discovery reachable from a single connection, carrying its own token.
    httpx_mock.add_response(json=_DBS)
    conn = DatasetteConnection("http://ds.test", "earthquakes", token="t")
    assert conn.databases() == ["earthquakes", "everest"]
    assert httpx_mock.get_requests()[0].headers["Authorization"] == "Bearer t"


def test_for_database_opens_sibling_with_same_url_and_token():
    conn = DatasetteConnection("http://ds.test/", "earthquakes", token="t")
    other = conn.for_database("everest")
    assert isinstance(other, DatasetteConnection)
    assert other.database_name == "everest"
    assert other._base_url == "http://ds.test"
    assert other._token == "t"
    conn.close()
    other.close()
