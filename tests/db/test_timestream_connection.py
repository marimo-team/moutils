"""Tests for the Amazon Timestream query adapter."""

import sys
from decimal import Decimal
from types import SimpleNamespace

import pytest

from moutils.db.timestream import TimestreamConnection


@pytest.fixture(autouse=True)
def _boto3_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace())


class FakeTimestream:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.calls = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return next(self.pages)


def test_timestream_paginates_and_decodes_values():
    columns = [
        {"Name": "n", "Type": {"ScalarType": "BIGINT"}},
        {"Name": "ratio", "Type": {"ScalarType": "DECIMAL"}},
        {
            "Name": "tags",
            "Type": {"ArrayColumnInfo": {"Type": {"ScalarType": "VARCHAR"}}},
        },
    ]
    client = FakeTimestream(
        [
            {
                "ColumnInfo": columns,
                "Rows": [
                    {
                        "Data": [
                            {"ScalarValue": "2"},
                            {"ScalarValue": "1.25"},
                            {"ArrayValue": [{"ScalarValue": "a"}]},
                        ]
                    }
                ],
                "NextToken": "next",
            },
            {
                "ColumnInfo": columns,
                "Rows": [
                    {
                        "Data": [
                            {"ScalarValue": "3"},
                            {"NullValue": True},
                            {"ArrayValue": []},
                        ]
                    }
                ],
            },
        ]
    )
    connection = TimestreamConnection(client, page_size=25)

    cursor = connection.cursor().execute("select * from metrics")

    assert cursor.fetchall() == [
        [2, Decimal("1.25"), ["a"]],
        [3, None, []],
    ]
    assert [column[1] for column in cursor.description] == [
        "BIGINT",
        "DECIMAL",
        "ARRAY<VARCHAR>",
    ]
    assert client.calls == [
        {"QueryString": "select * from metrics", "MaxRows": 25},
        {
            "QueryString": "select * from metrics",
            "MaxRows": 25,
            "NextToken": "next",
        },
    ]
