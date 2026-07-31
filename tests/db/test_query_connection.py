"""Tests for the generic query callable adapter."""

from types import SimpleNamespace

import pytest

from moutils.db.query import QueryConnection, QueryResult, normalize_result


def test_query_result_tuple_executes():
    connection = QueryConnection(
        lambda sql: (["value"], [[sql]], ["text"]), dialect="sqlite"
    )

    cursor = connection.cursor().execute("select 1")

    assert connection.dialect == "sqlite"
    assert cursor.fetchall() == [["select 1"]]
    assert cursor.description[0][1] == "text"


def test_record_mappings_preserve_first_record_order():
    result = normalize_result([{"b": 2, "a": 1}, {"b": 4, "a": 3}])

    assert list(result.columns) == ["b", "a"]
    assert list(result.rows) == [[2, 1], [4, 3]]


def test_record_mappings_include_fields_from_later_records():
    result = normalize_result([{"a": 1}, {"b": 2, "a": 3}, {"c": 4}])

    assert list(result.columns) == ["a", "b", "c"]
    assert list(result.rows) == [[1, None, None], [3, 2, None], [None, None, 4]]


def test_mapping_result():
    result = normalize_result({"columns": ["x"], "rows": [[1]], "types": ["int"]})
    assert result == QueryResult(["x"], [[1]], ["int"])


def test_polars_like_result():
    frame = SimpleNamespace(columns=["x"], dtypes=["Int64"], rows=lambda: [(1,)])
    result = normalize_result(frame)
    assert list(result.rows) == [(1,)]
    assert result.types == ["Int64"]


def test_arrow_like_result():
    frame = SimpleNamespace(
        column_names=["x"],
        schema=SimpleNamespace(types=["int64"]),
        to_pylist=lambda: [{"x": 1}],
    )
    result = normalize_result(frame)
    assert list(result.rows) == [[1]]
    assert result.types == ["int64"]


def test_schema_and_close_callbacks():
    closed = []
    connection = QueryConnection(
        lambda sql: ([], []),
        schema=lambda: [{"table": "t", "column": "x", "type": "int"}],
        close=lambda: closed.append(True),
    )
    assert connection.schema_rows()[0]["table"] == "t"
    connection.close()
    assert closed == [True]


def test_invalid_result_raises():
    with pytest.raises(TypeError, match="unsupported query result"):
        normalize_result(42)
