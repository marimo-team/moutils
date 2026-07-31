"""Read-only marimo SQL connection for Datasette."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    import httpx

from ._core import Connection

# One round-trip that yields (table, column, type) for every user table, using
# SQLite's table-valued pragma function joined against sqlite_master.
_SCHEMA_SQL = (
    'select m.name as "table", p.name as "column", p.type as "type" '
    "from sqlite_master m join pragma_table_info(m.name) p "
    "where m.type = 'table' and m.name not like 'sqlite_%' "
    "order by m.name, p.cid"
)


def _require_httpx() -> Any:
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - exercised only without httpx
        raise ImportError(
            "DatasetteConnection requires httpx. "
            "Install it with `pip install moutils[db]`."
        ) from exc
    return httpx


class DatasetteConnection(Connection):
    """Connect to one database in a Datasette instance.

    Set ``token`` for bearer-token authentication. Datasette can limit query
    results. This connection warns when the server truncates a result.
    """

    dialect = "sqlite"

    def __init__(
        self,
        base_url: str,
        database: str,
        token: str | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._database = database
        self._token = token
        self.database_name = database  # marimo catalog uses this as the DB label
        # Reuse one client for connection pooling; only close what we created.
        self._owns_client = client is None
        self._client = client or _require_httpx().Client(timeout=120)

    def _run_sql(self, sql: str) -> dict:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        database = quote(self._database, safe="")
        # Datasette 0.x uses this URL. Datasette 1.x redirects it to
        # /<database>/-/query.json, so follow that redirect for compatibility.
        resp = self._client.get(
            f"{self._base_url}/{database}.json",
            params={"sql": sql, "_shape": "arrays", "_extra": "columns"},
            headers=headers,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("unexpected Datasette response: expected an object")
        if data.get("ok") is False:
            raise ValueError(
                f"Datasette query failed: {data.get('error', 'unknown error')}"
            )
        return data

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return columns and rows for the shared cursor."""
        data = self._run_sql(query)
        if data.get("truncated"):
            warnings.warn(
                "Datasette truncated the result set at max_returned_rows. "
                "Add a LIMIT to your query (or raise Datasette's "
                "max_returned_rows) to fetch the rest.",
                stacklevel=3,
            )
        columns = data.get("columns")
        rows = data.get("rows")
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise ValueError("unexpected Datasette query response shape")
        return columns, rows, None

    def schema_rows(self) -> list[dict[str, Any]]:
        """Return the columns and types for each user table."""
        data = self._run_sql(_SCHEMA_SQL)
        columns = data.get("columns")
        rows = data.get("rows")
        if columns != ["table", "column", "type"] or rows is None:
            raise ValueError(f"unexpected schema response shape: columns={columns!r}")
        return [
            {
                "table": str(table),
                "column": str(column),
                "type": None if type_ is None else str(type_),
            }
            for table, column, type_ in rows
        ]

    def databases(self) -> list[str]:
        """Return the databases on this Datasette instance."""
        return databases(self._base_url, self._token, client=self._client)

    def for_database(self, database: str) -> "DatasetteConnection":
        """Connect to another database with the same HTTP client."""
        return DatasetteConnection(
            self._base_url,
            database,
            token=self._token,
            client=self._client,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def databases(
    base_url: str,
    token: str | None = None,
    *,
    client: httpx.Client | None = None,
) -> list[str]:
    """Return the database routes on a Datasette instance."""
    owns = client is None
    client = client or _require_httpx().Client(timeout=120)
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = client.get(f"{base_url.rstrip('/')}/-/databases.json", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("databases") if isinstance(data, dict) else data
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) for entry in entries
        ):
            raise ValueError("unexpected Datasette databases response shape")
        routes = [entry.get("route") for entry in entries if not entry.get("is_memory")]
        if not all(isinstance(route, str) for route in routes):
            raise ValueError("unexpected Datasette database route")
        return routes
    finally:
        if owns:
            client.close()
