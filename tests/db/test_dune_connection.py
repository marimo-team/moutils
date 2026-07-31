"""Tests for the Dune raw SQL adapter."""

import sys
from types import SimpleNamespace

import pytest

from moutils.db.dune import DuneConnection


@pytest.fixture(autouse=True)
def _dune_client_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "dune_client", SimpleNamespace())


def _result(rows, next_offset=None):
    metadata = SimpleNamespace(column_names=["name"], column_types=["varchar"])
    return SimpleNamespace(
        result=SimpleNamespace(rows=rows, metadata=metadata),
        next_offset=next_offset,
    )


class FakeDune:
    def __init__(self, states, results):
        self.states = iter(states)
        self.results = iter(results)
        self.execute_calls = []
        self.result_calls = []

    def execute_sql(self, **kwargs):
        self.execute_calls.append(kwargs)
        return SimpleNamespace(execution_id="job")

    def get_execution_status(self, execution_id):
        state = next(self.states)
        return SimpleNamespace(state=SimpleNamespace(value=state), error=None)

    def get_execution_results(self, execution_id, **kwargs):
        self.result_calls.append((execution_id, kwargs))
        return next(self.results)


def test_dune_waits_and_paginates():
    client = FakeDune(
        ["QUERY_STATE_EXECUTING", "QUERY_STATE_COMPLETED"],
        [_result([{"name": "Ada"}], 1), _result([{"name": "Grace"}])],
    )
    connection = DuneConnection(
        client,
        performance="medium",
        poll_interval=0,
        batch_size=1,
    )

    cursor = connection.cursor().execute("select name from people")

    assert cursor.fetchall() == [["Ada"], ["Grace"]]
    assert cursor.description[0][1] == "varchar"
    assert client.execute_calls == [
        {"query_sql": "select name from people", "performance": "medium"}
    ]
    assert client.result_calls == [
        ("job", {"limit": 1, "offset": 0}),
        ("job", {"limit": 1, "offset": 1}),
    ]


def test_dune_failure_raises():
    client = FakeDune(["QUERY_STATE_FAILED"], [])
    with pytest.raises(RuntimeError, match="QUERY_STATE_FAILED"):
        DuneConnection(client, poll_interval=0).cursor().execute("select 1")
