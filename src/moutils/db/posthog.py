"""DB-API 2.0 connection over PostHog's HogQL query API.

Built on :mod:`moutils.db._core`: paging/``description`` live in the shared
``Cursor``, so this module only owns the HTTP transport, the HogQL result mapping
(``_fetch``), and schema discovery.

Schema discovery goes through ``DatabaseSchemaQuery`` — the same authed POST the
PostHog UI uses to build its schema tree. It does **not** swallow failures: an
HTTP error propagates, and an unexpected response shape raises ``ValueError``.
Fail early rather than hand back a stale, made-up table list.
"""

from typing import Any

import requests

from ._core import Connection


class PostHogConnection(Connection):
    """DB-API 2.0 connection over the PostHog HogQL API.

    ``dialect`` tells marimo to parse queries as ClickHouse, which HogQL is
    closely modelled on, and makes marimo detect the connection as a SQL engine.
    """

    dialect = "clickhouse"

    def __init__(
        self,
        api_key: str,
        project_id: str | int,
        host: str = "https://us.posthog.com",
    ) -> None:
        self._api_key = api_key
        self._project_id = str(project_id)  # accept int, normalise for the URL
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
        return resp.json()

    def _run_hogql(self, query: str) -> dict:
        return self._run_query({"kind": "HogQLQuery", "query": query})

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return ``(columns, rows, types)`` for the shared cursor.

        `types` is HogQL's list of ``[name, clickhouse_type]`` pairs when present
        (or None); the cursor turns it into DB-API type codes.
        """
        data = self._run_hogql(query)
        return data.get("columns") or [], data.get("results", []), data.get("types")

    def schema_rows(self) -> list[dict[str, Any]]:
        """Return HogQL table/column/type rows (via ``DatabaseSchemaQuery``)."""
        return schema_rows(self)


def _rows_from_schema_response(data: dict) -> list[dict[str, Any]]:
    """Flatten a DatabaseSchemaQuery reply into table/column/type rows.

    Raises ``ValueError`` on any shape we don't recognise.
    """
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
    """Return table/column/type rows for the connection.

    Propagates HTTP errors and raises ``ValueError`` on an unexpected response
    shape — no fallback, no silent degradation.
    """
    data = conn._run_query({"kind": "DatabaseSchemaQuery"})
    return _rows_from_schema_response(data)
