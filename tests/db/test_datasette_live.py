"""End-to-end tests with an in-process Datasette instance."""

import httpx
import pytest


def test_execute_real(live_conn):
    cur = live_conn.cursor().execute("select id, name, age from dogs order by id")
    assert [d[0] for d in cur.description] == ["id", "name", "age"]
    assert cur.fetchall() == [[1, "Cleo", 5], [2, "Pancakes", 3]]


def test_fetchone_paging_real(live_conn):
    cur = live_conn.cursor().execute("select name from dogs order by id")
    assert cur.fetchone() == ["Cleo"]
    assert cur.fetchone() == ["Pancakes"]
    assert cur.fetchone() is None


def test_schema_rows_real(live_conn):
    rows = live_conn.schema_rows()
    assert {"table": "dogs", "column": "name", "type": "TEXT"} in rows
    assert {"table": "dogs", "column": "age", "type": "INTEGER"} in rows
    assert {r["table"] for r in rows} == {"dogs", "cats"}


def test_sql_error_real(live_conn):
    with pytest.raises(httpx.HTTPStatusError):
        live_conn.cursor().execute("select * from does_not_exist")


def test_databases_real(live_conn):
    # live_conn activates routing into the in-process Datasette (serving one db).
    from moutils.db.datasette import databases

    assert databases("http://datasette.test") == ["sample"]
