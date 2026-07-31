"""Tests for the Cloudflare D1 REST connection."""

import responses

from moutils.db.d1 import D1Connection

_URL = "https://api.cloudflare.com/client/v4/accounts/acct/d1/database/db/raw"


def _response(columns, rows):
    return {
        "success": True,
        "result": [{"success": True, "results": {"columns": columns, "rows": rows}}],
    }


@responses.activate
def test_d1_query_and_auth():
    responses.post(_URL, json=_response(["name", "n"], [["Ada", 1]]))
    connection = D1Connection("acct", "db", "token")

    cursor = connection.cursor().execute("select name, n from people")

    assert cursor.fetchall() == [["Ada", 1]]
    request = responses.calls[0].request
    assert request.headers["Authorization"] == "Bearer token"
    assert request.body == b'{"sql": "select name, n from people"}'
    connection.close()


@responses.activate
def test_d1_schema_rows():
    responses.post(
        _URL,
        json=_response(
            ["table", "column", "type"],
            [["people", "name", "TEXT"], ["people", "age", "INTEGER"]],
        ),
    )
    connection = D1Connection("acct", "db", "token")
    assert connection.schema_rows() == [
        {"table": "people", "column": "name", "type": "TEXT"},
        {"table": "people", "column": "age", "type": "INTEGER"},
    ]
