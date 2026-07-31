"""Tests for the ConnectorX adapter without installing ConnectorX."""

import sys
from types import SimpleNamespace

import pytest

from moutils.db.connectorx import ConnectorXConnection


def test_connectorx_infers_dialect_and_forwards_options(monkeypatch):
    calls = []

    def read_sql(connection, query, **options):
        calls.append((connection, query, options))
        return (["x"], [[1]])

    monkeypatch.setitem(sys.modules, "connectorx", SimpleNamespace(read_sql=read_sql))
    monkeypatch.setitem(sys.modules, "polars", SimpleNamespace())
    connection = ConnectorXConnection(
        "postgresql://localhost/db", return_type="polars", protocol="binary"
    )

    assert connection.dialect == "postgres"
    assert connection.cursor().execute("select 1").fetchall() == [[1]]
    assert calls == [
        (
            "postgresql://localhost/db",
            "select 1",
            {"return_type": "polars", "protocol": "binary"},
        )
    ]


def test_connectorx_federated_requires_dialect(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "connectorx", SimpleNamespace(read_sql=lambda: None)
    )
    with pytest.raises(ValueError, match="dialect is required"):
        ConnectorXConnection({"one": "postgresql://localhost/one"})
