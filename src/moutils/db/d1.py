"""Marimo SQL connection for Cloudflare D1's REST API."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from ._core import Connection

_SCHEMA_SQL = (
    'select m.name as "table", p.name as "column", p.type as "type" '
    "from sqlite_schema m join pragma_table_info(m.name) p "
    "where m.type = 'table' and m.name not like 'sqlite_%' "
    "order by m.name, p.cid"
)


class D1Connection(Connection):
    """Connect to one Cloudflare D1 database over HTTP.

    Use an API token with only the ``D1 Read`` permission when the connection
    should be read-only.
    """

    dialect = "sqlite"

    def __init__(
        self,
        account_id: str,
        database_id: str,
        api_token: str,
        *,
        session: requests.Session | None = None,
        base_url: str = "https://api.cloudflare.com/client/v4",
    ) -> None:
        self._account_id = account_id
        self._database_id = database_id
        self._api_token = api_token
        self._base_url = base_url.rstrip("/")
        self._owns_session = session is None
        self._session = session or requests.Session()

    def _run_sql(self, query: str) -> dict[str, Any]:
        account = quote(self._account_id, safe="")
        database = quote(self._database_id, safe="")
        response = self._session.post(
            f"{self._base_url}/accounts/{account}/d1/database/{database}/raw",
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
            json={"sql": query},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("unexpected D1 response: expected an object")
        if data.get("success") is not True:
            raise ValueError(f"D1 query failed: {data.get('errors', [])!r}")
        results = data.get("result")
        if not isinstance(results, list) or len(results) != 1:
            raise ValueError("D1 connection requires exactly one SQL statement")
        result = results[0]
        if not isinstance(result, dict) or result.get("success") is not True:
            raise ValueError("D1 statement failed")
        return result

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        result = self._run_sql(query).get("results")
        if not isinstance(result, dict):
            raise ValueError("unexpected D1 result shape")
        columns = result.get("columns")
        rows = result.get("rows")
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise ValueError("unexpected D1 rows or columns")
        return columns, rows, None

    def schema_rows(self) -> list[dict[str, Any]]:
        columns, rows, _ = self._fetch(_SCHEMA_SQL)
        if columns != ["table", "column", "type"]:
            raise ValueError(f"unexpected D1 schema columns: {columns!r}")
        return [
            {
                "table": str(table),
                "column": str(column),
                "type": None if type_ is None else str(type_),
            }
            for table, column, type_ in rows
        ]

    def close(self) -> None:
        if self._owns_session:
            self._session.close()
