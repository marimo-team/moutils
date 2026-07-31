"""Marimo SQL connection for the Elasticsearch Python client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._core import Connection
from ._dependencies import require_dependency


def _body(response: Any) -> Mapping[str, Any]:
    body = getattr(response, "body", response)
    if not isinstance(body, Mapping):
        raise ValueError("unexpected Elasticsearch response shape")
    return body


class ElasticsearchConnection(Connection):
    """Run Elasticsearch SQL through an existing ``Elasticsearch`` client."""

    dialect = "sql"

    def __init__(
        self,
        client: Any,
        *,
        fetch_size: int = 1_000,
        close_client: bool = False,
    ) -> None:
        require_dependency("elasticsearch", connection_name="ElasticsearchConnection")
        if isinstance(fetch_size, bool) or not isinstance(fetch_size, int):
            raise TypeError("fetch_size must be an integer")
        if fetch_size < 1:
            raise ValueError("fetch_size must be positive")
        self._client = client
        self._fetch_size = fetch_size
        self._close_client = close_client

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        response = self._client.sql.query(query=query, fetch_size=self._fetch_size)
        columns: list[Any] | None = None
        types: list[Any] | None = None
        rows: list[Any] = []
        cursor: str | None = None
        try:
            while True:
                data = _body(response)
                if columns is None:
                    schema = data.get("columns")
                    if not isinstance(schema, list):
                        raise ValueError("Elasticsearch response has no columns")
                    if not all(isinstance(column, Mapping) for column in schema):
                        raise ValueError("unexpected Elasticsearch columns")
                    columns = [column.get("name") for column in schema]
                    types = [column.get("type") for column in schema]
                page_rows = data.get("rows", [])
                if not isinstance(page_rows, list):
                    raise ValueError("unexpected Elasticsearch rows")
                rows.extend(page_rows)
                cursor = data.get("cursor")
                if not cursor:
                    break
                response = self._client.sql.query(cursor=cursor)
            return columns, rows, types
        finally:
            if cursor:
                try:
                    self._client.sql.clear_cursor(cursor=cursor)
                except Exception:
                    pass  # Do not hide the query error with a cleanup failure.

    def close(self) -> None:
        if self._close_client:
            self._client.close()
