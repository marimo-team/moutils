"""Adapt a query callable into a marimo-compatible DB-API connection."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ._core import Connection


@dataclass(frozen=True)
class QueryResult:
    """A provider-independent tabular query result."""

    columns: Sequence[Any]
    rows: Iterable[Sequence[Any]]
    types: Sequence[Any] | None = None


def _records_result(records: list[Mapping[Any, Any]]) -> QueryResult:
    if not records:
        return QueryResult([], [])
    columns = list(records[0])
    return QueryResult(
        columns, ([record.get(column) for column in columns] for record in records)
    )


def normalize_result(result: Any) -> QueryResult:
    """Normalize common tabular values returned by query libraries.

    Supported values are :class:`QueryResult`, ``(columns, rows[, types])``
    tuples, mappings with ``columns`` and ``rows`` keys, record mappings,
    pandas/Polars dataframes, and PyArrow tables.
    """
    if isinstance(result, QueryResult):
        return result

    if isinstance(result, tuple) and len(result) in (2, 3):
        columns, rows = result[:2]
        types = result[2] if len(result) == 3 else None
        return QueryResult(columns, rows, types)

    if isinstance(result, Mapping):
        if "columns" not in result or "rows" not in result:
            raise TypeError("query result mapping must contain 'columns' and 'rows'")
        return QueryResult(result["columns"], result["rows"], result.get("types"))

    # PyArrow Table: to_pylist returns records while schema preserves types.
    if hasattr(result, "column_names") and callable(getattr(result, "to_pylist", None)):
        columns = list(result.column_names)
        records = result.to_pylist()
        rows = ([record.get(column) for column in columns] for record in records)
        schema = getattr(result, "schema", None)
        types = [str(type_) for type_ in schema.types] if schema is not None else None
        return QueryResult(columns, rows, types)

    columns = getattr(result, "columns", None)
    if columns is not None:
        columns = list(columns)

        # Polars DataFrame.
        rows_method = getattr(result, "rows", None)
        if callable(rows_method):
            types = getattr(result, "dtypes", None)
            return QueryResult(
                columns,
                rows_method(),
                [str(type_) for type_ in types] if types is not None else None,
            )

        # pandas DataFrame and compatible objects.
        tuples = getattr(result, "itertuples", None)
        if callable(tuples):
            dtypes = getattr(result, "dtypes", None)
            return QueryResult(
                columns,
                tuples(index=False, name=None),
                [str(type_) for type_ in dtypes] if dtypes is not None else None,
            )

    if isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
        records = list(result)
        if not records:
            return QueryResult([], [])
        if all(isinstance(record, Mapping) for record in records):
            return _records_result(records)

    raise TypeError(
        "unsupported query result; return QueryResult, a result tuple, records, "
        "or a pandas, Polars, or PyArrow table"
    )


class QueryConnection(Connection):
    """Wrap ``query(sql) -> tabular result`` for use in marimo SQL cells."""

    def __init__(
        self,
        query: Callable[[str], Any],
        *,
        dialect: str = "sql",
        schema: Callable[[], list[dict[str, Any]]] | None = None,
        close: Callable[[], Any] | None = None,
    ) -> None:
        if not callable(query):
            raise TypeError("query must be callable")
        self._query = query
        self.dialect = dialect
        self._schema = schema
        self._close = close

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        result = normalize_result(self._query(query))
        return list(result.columns), [list(row) for row in result.rows], result.types

    def schema_rows(self) -> list[dict[str, Any]]:
        return [] if self._schema is None else self._schema()

    def close(self) -> None:
        if self._close is not None:
            self._close()
