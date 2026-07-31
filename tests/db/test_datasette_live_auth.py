"""End-to-end tests for Datasette token authentication."""

import httpx
import pytest

from moutils.db.datasette import DatasetteConnection

_HOST = "http://datasette.test"
_DB = "sample"


def test_no_token_is_denied(route_authed):
    conn = DatasetteConnection(_HOST, _DB)  # no token
    with pytest.raises(httpx.HTTPStatusError) as exc:
        conn.cursor().execute("select 1")
    assert exc.value.response.status_code == 403
    conn.close()


def test_wrong_token_is_denied(route_authed):
    conn = DatasetteConnection(_HOST, _DB, token="not-the-token")
    with pytest.raises(httpx.HTTPStatusError) as exc:
        conn.cursor().execute("select 1")
    assert exc.value.response.status_code == 403
    conn.close()


def test_correct_token_grants_access(route_authed, live_token):
    conn = DatasetteConnection(_HOST, _DB, token=live_token)
    assert conn.cursor().execute("select name from dogs order by id").fetchall() == [
        ["Cleo"],
        ["Pancakes"],
    ]
    assert {"table": "dogs", "column": "name", "type": "TEXT"} in conn.schema_rows()
    conn.close()
