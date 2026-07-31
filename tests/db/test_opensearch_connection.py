"""Tests for the OpenSearch SQL adapter."""

import sys
from types import SimpleNamespace

import pytest

from moutils.db.opensearch import OpenSearchConnection


@pytest.fixture(autouse=True)
def _opensearch_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "opensearchpy", SimpleNamespace())


class FakeTransport:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def perform_request(self, method, path, *, body):
        self.calls.append((method, path, body))
        return next(self.pages)


def test_opensearch_paginates_jdbc_results():
    transport = FakeTransport(
        [
            {
                "schema": [{"name": "name", "type": "keyword"}],
                "datarows": [["Ada"]],
                "cursor": "next",
            },
            {"datarows": [["Grace"]]},
        ]
    )
    connection = OpenSearchConnection(
        SimpleNamespace(transport=transport), fetch_size=5
    )

    cursor = connection.cursor().execute("select name from people")

    assert cursor.fetchall() == [["Ada"], ["Grace"]]
    assert cursor.description[0][1] == "keyword"
    assert transport.calls == [
        (
            "POST",
            "/_plugins/_sql",
            {"query": "select name from people", "fetch_size": 5},
        ),
        ("POST", "/_plugins/_sql", {"cursor": "next"}),
    ]
