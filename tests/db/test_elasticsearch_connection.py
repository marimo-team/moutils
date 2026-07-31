"""Tests for the Elasticsearch SQL adapter."""

import sys
from types import SimpleNamespace

import pytest

from moutils.db.elasticsearch import ElasticsearchConnection


@pytest.fixture(autouse=True)
def _elasticsearch_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "elasticsearch", SimpleNamespace())


class FakeSQL:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.queries = []
        self.cleared = []

    def query(self, **kwargs):
        self.queries.append(kwargs)
        return SimpleNamespace(body=next(self.pages))

    def clear_cursor(self, *, cursor):
        self.cleared.append(cursor)


def test_elasticsearch_paginates():
    sql = FakeSQL(
        [
            {
                "columns": [{"name": "name", "type": "keyword"}],
                "rows": [["Ada"]],
                "cursor": "next",
            },
            {"rows": [["Grace"]]},
        ]
    )
    connection = ElasticsearchConnection(SimpleNamespace(sql=sql), fetch_size=10)

    cursor = connection.cursor().execute("select name from people")

    assert cursor.fetchall() == [["Ada"], ["Grace"]]
    assert cursor.description[0][1] == "keyword"
    assert sql.queries == [
        {"query": "select name from people", "fetch_size": 10},
        {"cursor": "next"},
    ]
    assert sql.cleared == []


def test_elasticsearch_clears_cursor_after_error():
    sql = FakeSQL(
        [
            {
                "columns": [{"name": "name", "type": "keyword"}],
                "rows": [],
                "cursor": "next",
            },
            {"rows": "bad"},
        ]
    )
    with pytest.raises(ValueError, match="rows"):
        ElasticsearchConnection(SimpleNamespace(sql=sql)).cursor().execute("select 1")
    assert sql.cleared == ["next"]
