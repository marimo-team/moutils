"""Tests for the Datasette HTTP contract."""

import httpx
import pytest

from moutils.db.datasette import DatasetteConnection


def test_execute_builds_request_and_parses(httpx_mock):
    httpx_mock.add_response(
        json={
            "ok": True,
            "columns": ["id", "name"],
            "rows": [[1, "Cleo"], [2, "Pancakes"]],
            "truncated": False,
        },
    )
    conn = DatasetteConnection("http://ds.test", "content", token="sekret")
    cur = conn.cursor().execute("select id, name from dogs")

    assert [d[0] for d in cur.description] == ["id", "name"]
    # SQLite results carry no per-column types -> None type codes.
    assert [d[1] for d in cur.description] == [None, None]
    assert cur.fetchall() == [[1, "Cleo"], [2, "Pancakes"]]

    req = httpx_mock.get_requests()[0]
    assert req.method == "GET"
    assert str(req.url).startswith("http://ds.test/content.json")
    assert req.url.params["sql"] == "select id, name from dogs"
    assert req.url.params["_shape"] == "arrays"
    assert req.url.params["_extra"] == "columns"
    assert req.headers["Authorization"] == "Bearer sekret"


def test_execute_follows_datasette_1_query_redirect(httpx_mock):
    httpx_mock.add_response(
        status_code=302,
        headers={
            "Location": "/content/-/query.json?sql=select+1&_shape=arrays&_extra=columns"
        },
    )
    httpx_mock.add_response(
        json={"ok": True, "columns": ["n"], "rows": [[1]], "truncated": False}
    )

    conn = DatasetteConnection("http://ds.test", "content", token="sekret")
    assert conn.cursor().execute("select 1").fetchall() == [[1]]

    requests = httpx_mock.get_requests()
    assert requests[1].url.path == "/content/-/query.json"
    assert requests[1].headers["Authorization"] == "Bearer sekret"


def test_database_route_is_url_encoded(httpx_mock):
    httpx_mock.add_response(json={"ok": True, "columns": [], "rows": []})
    DatasetteConnection("http://ds.test", "one/two").cursor().execute("select 1")
    assert httpx_mock.get_requests()[0].url.raw_path.startswith(b"/one%2Ftwo.json")


def test_no_token_omits_auth_and_strips_trailing_slash(httpx_mock):
    httpx_mock.add_response(json={"ok": True, "columns": [], "rows": []})
    conn = DatasetteConnection("http://ds.test/", "content")  # trailing slash
    conn.cursor().execute("select 1")

    req = httpx_mock.get_requests()[0]
    assert "authorization" not in req.headers
    url = str(req.url)
    assert url.startswith("http://ds.test/content.json")
    assert "//content" not in url


def test_truncated_emits_warning(httpx_mock):
    httpx_mock.add_response(
        json={"ok": True, "columns": ["n"], "rows": [[1]], "truncated": True},
    )
    conn = DatasetteConnection("http://ds.test", "content")
    with pytest.warns(UserWarning, match="truncated"):
        conn.cursor().execute("select 1")


def test_bad_query_shape_raises(httpx_mock):
    httpx_mock.add_response(json={"ok": True, "rows": []})
    with pytest.raises(ValueError, match="query response shape"):
        DatasetteConnection("http://ds.test", "content").cursor().execute("select 1")


@pytest.mark.parametrize("status", [400, 500])
def test_http_error_propagates(httpx_mock, status):
    httpx_mock.add_response(status_code=status, json={"ok": False, "error": "boom"})
    with pytest.raises(httpx.HTTPStatusError):
        DatasetteConnection("http://ds.test", "content").cursor().execute("select bad")


def test_commit_rollback_are_noops():
    conn = DatasetteConnection("http://ds.test", "content")
    assert conn.commit() is None
    assert conn.rollback() is None


def test_dialect_is_sqlite():
    assert DatasetteConnection("http://ds.test", "content").dialect == "sqlite"
