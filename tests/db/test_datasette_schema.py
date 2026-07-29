"""Schema discovery — pragma-based parsing; fails early on unexpected shape."""

import pytest

from moutils.db.datasette import DatasetteConnection


def _schema_response(rows):
    return {
        "ok": True,
        "columns": ["table", "column", "type"],
        "rows": rows,
        "truncated": False,
    }


def test_schema_rows_parses(httpx_mock):
    httpx_mock.add_response(
        json=_schema_response(
            [
                ["dogs", "id", "INTEGER"],
                ["dogs", "name", "TEXT"],
                ["cats", "nickname", "TEXT"],
            ]
        )
    )
    rows = DatasetteConnection("http://ds.test", "content").schema_rows()

    assert {"table": "dogs", "column": "id", "type": "INTEGER"} in rows
    assert {r["table"] for r in rows} == {"dogs", "cats"}
    assert len(rows) == 3

    # outbound query uses the table-valued pragma introspection.
    req = httpx_mock.get_requests()[0]
    assert "pragma_table_info" in req.url.params["sql"]


def test_schema_bad_shape_raises(httpx_mock):
    httpx_mock.add_response(json={"ok": True, "columns": ["x"], "rows": [["y"]]})
    with pytest.raises(ValueError):
        DatasetteConnection("http://ds.test", "content").schema_rows()


def test_empty_schema_is_ok(httpx_mock):
    httpx_mock.add_response(json=_schema_response([]))
    assert DatasetteConnection("http://ds.test", "content").schema_rows() == []
