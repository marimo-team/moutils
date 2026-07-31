"""Tests for the shared cursor."""

import pytest

from moutils.db._core import Connection


class FakeConnection(Connection):
    """A Connection whose ``_fetch`` returns a fixed triple."""

    dialect = "fake"

    def __init__(self, triple):
        self._triple = triple

    def _fetch(self, query):
        return self._triple

    def schema_rows(self):
        return []


def cursor_for(triple):
    return FakeConnection(triple).cursor()


@pytest.fixture
def five_rows():
    return (
        ["date", "n"],
        [
            ["2026-01-01", 5],
            ["2026-01-02", 8],
            ["2026-01-03", 3],
            ["2026-01-04", 1],
            ["2026-01-05", 9],
        ],
        [["date", "Date"], ["n", "UInt64"]],
    )


def test_description_from_columns_and_types():
    cur = cursor_for(
        (["date", "n"], [["2026-01-01", 5]], [["date", "Date"], ["n", "UInt64"]])
    ).execute("SELECT 1")

    assert len(cur.description) == 2
    for desc in cur.description:
        assert len(desc) == 7  # DB-API 2.0 7-tuple
    assert [d[0] for d in cur.description] == ["date", "n"]
    assert [d[1] for d in cur.description] == ["Date", "UInt64"]
    for desc in cur.description:
        assert desc[2:] == (None, None, None, None, None)


def test_description_names_are_str():
    cur = cursor_for(([1, 2], [], [["a", "Int64"], ["b", "Int64"]])).execute("SELECT 1")
    assert [d[0] for d in cur.description] == ["1", "2"]


def test_types_none_gives_none_type_codes():
    cur = cursor_for((["a", "b"], [["x", "y"]], None)).execute("SELECT 1")
    assert [d[1] for d in cur.description] == [None, None]


def test_bare_string_type_passes_through():
    # A `types` entry that's a bare string (not a [name, type] pair) is passed
    # through unchanged — exercises the isinstance/len>1 branch.
    cur = cursor_for((["a", "b"], [], ["Int64", ["b", "String"]])).execute("SELECT 1")
    assert [d[1] for d in cur.description] == ["Int64", "String"]


def test_missing_type_keeps_column_in_description():
    cur = cursor_for((["a", "b"], [[1, 2]], ["Int64"])).execute("SELECT 1")
    assert [d[0] for d in cur.description] == ["a", "b"]
    assert [d[1] for d in cur.description] == ["Int64", None]


def test_rowcount_matches_rows(five_rows):
    cur = cursor_for(five_rows).execute("SELECT 1")
    assert cur.rowcount == 5


def test_paging_shares_pos(five_rows):
    cur = cursor_for(five_rows).execute("SELECT 1")
    assert cur.arraysize == 1

    assert cur.fetchone() == ["2026-01-01", 5]
    assert cur.fetchmany() == [["2026-01-02", 8]]  # arraysize == 1
    assert cur.fetchmany(3) == [
        ["2026-01-03", 3],
        ["2026-01-04", 1],
        ["2026-01-05", 9],
    ]
    assert cur.fetchall() == []  # nothing left
    assert cur.fetchone() is None


def test_fetchall_returns_from_current_pos(five_rows):
    cur = cursor_for(five_rows).execute("SELECT 1")
    cur.fetchone()
    assert cur.fetchall() == [
        ["2026-01-02", 8],
        ["2026-01-03", 3],
        ["2026-01-04", 1],
        ["2026-01-05", 9],
    ]


def test_close_empties_rows_and_resets_pos(five_rows):
    cur = cursor_for(five_rows).execute("SELECT 1")
    cur.fetchone()
    cur.close()
    assert cur.fetchall() == []
    assert cur.fetchone() is None


def test_parameters_guard_raises(five_rows):
    cur = cursor_for(five_rows)
    with pytest.raises(NotImplementedError, match="do not support bound parameters"):
        cur.execute("SELECT 1", parameters=[1])


def test_parameters_none_or_empty_ok(five_rows):
    cur = cursor_for(five_rows)
    cur.execute("SELECT 1", parameters=None)
    cur.execute("SELECT 1", parameters=[])  # empty is falsy -> allowed


def test_connection_is_abstract():
    # A subclass missing a hook can't be instantiated (Connection is an ABC).
    class Incomplete(Connection):
        dialect = "fake"

        def _fetch(self, query):  # schema_rows still missing
            return ([], [], None)

    with pytest.raises(TypeError):
        Incomplete()
