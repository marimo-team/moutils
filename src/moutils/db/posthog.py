"""Read-only marimo SQL connection for PostHog HogQL."""

from typing import Any

import requests

from ._core import Connection

_MAX_PAGE_SIZE = 50_000


class PostHogConnection(Connection):
    """Connect to a PostHog project with a personal API key.

    ``page_size`` caps each query result and must be from 1 through 50,000.
    """

    dialect = "clickhouse"

    def __init__(
        self,
        api_key: str,
        project_id: str | int,
        *,
        page_size: int,
        host: str = "https://us.posthog.com",
    ) -> None:
        if isinstance(page_size, bool) or not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if not 1 <= page_size <= _MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be between 1 and {_MAX_PAGE_SIZE:,}")
        self._api_key = api_key
        self._project_id = str(project_id)  # accept int, normalise for the URL
        self._page_size = page_size
        self._host = host.rstrip("/")

    def _run_query(self, query: dict) -> dict:
        resp = requests.post(
            f"{self._host}/api/projects/{self._project_id}/query/",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={"query": query},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("unexpected PostHog response: expected an object")
        return data

    def _run_hogql(self, query: str) -> dict:
        query = query.strip().rstrip(";").rstrip()
        paged_query = f"SELECT * FROM ({query}) AS moutils_page LIMIT {self._page_size}"
        return self._run_query({"kind": "HogQLQuery", "query": paged_query})

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return columns, rows, and types for the shared cursor."""
        data = self._run_hogql(query)
        columns = data.get("columns")
        rows = data.get("results")
        types = data.get("types")
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise ValueError("unexpected PostHog query response shape")
        if types is not None and not isinstance(types, list):
            raise ValueError("unexpected PostHog query types")
        return columns, rows, types

    def schema_rows(self) -> list[dict[str, Any]]:
        """Return HogQL table/column/type rows (via ``DatabaseSchemaQuery``)."""
        return schema_rows(self)


def _rows_from_schema_response(data: dict) -> list[dict[str, Any]]:
    """Convert a schema response to table, column, and type rows."""
    tables = data.get("tables")
    if not isinstance(tables, dict) or not tables:
        raise ValueError("DatabaseSchemaQuery response has no 'tables' mapping")

    rows: list[dict[str, Any]] = []
    for table_key, table_info in tables.items():
        if not isinstance(table_info, dict):
            raise ValueError(f"table {table_key!r} is not an object")
        table_name = table_info.get("name", table_key)
        fields = table_info.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"table {table_key!r} has no 'fields' mapping")
        for field_key, field_info in fields.items():
            if isinstance(field_info, dict):
                column = field_info.get("name", field_key)
                type_ = field_info.get("type")
            else:
                column, type_ = field_key, None
            rows.append(
                {
                    "table": str(table_name),
                    "column": str(column),
                    "type": None if type_ is None else str(type_),
                }
            )

    if not rows:
        raise ValueError("DatabaseSchemaQuery response contained no columns")
    return rows


def schema_rows(conn: Any) -> list[dict[str, Any]]:
    """Return the table, column, and type rows for a connection."""
    data = conn._run_query({"kind": "DatabaseSchemaQuery"})
    return _rows_from_schema_response(data)
