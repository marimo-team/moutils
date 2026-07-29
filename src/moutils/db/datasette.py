"""DB-API 2.0 connection over a Datasette instance's JSON query API.

Built on :mod:`moutils.db._core`: paging/``description`` live in the shared
``Cursor``, so this module only owns the ``httpx`` transport, the result mapping
(``_fetch``), and schema discovery.

Datasette serves SQLite over an HTTP JSON API. Arbitrary SQL goes to
``GET {base_url}/{database}.json?sql=...&_shape=arrays``, which returns a
``{"columns": [...], "rows": [[...]], "truncated": bool, "ok": bool}`` envelope;
SQL errors come back as HTTP 4xx with ``{"ok": false, "error": "..."}``.

``httpx`` is an optional dependency (install with ``pip install moutils[db]``); it
is imported lazily so importing this module never requires it — only constructing
a :class:`DatasetteConnection` (or calling :func:`databases`) does.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

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
    """DB-API 2.0 connection over **one** database of a Datasette instance.

    A connection is scoped to a single database because that's how Datasette
    scopes SQL: queries go to ``{base_url}/{database}.json?sql=...``, and one
    database can't reach another's tables. ``dialect="sqlite"`` makes marimo
    parse cells as SQLite and detect the connection as a SQL engine.

    Discovering the other databases on the same instance
    ----------------------------------------------------
    A Datasette instance usually serves several databases. From a single
    connection you can list its siblings and open one of them::

        conn = DatasetteConnection("https://example.com", "earthquakes")
        conn.databases()                       # -> ['earthquakes', 'everest', ...]
        everest = conn.for_database("everest") # a new connection to another db

    ``databases()`` uses Datasette's ``/-/databases.json`` introspection endpoint
    (carrying this connection's token). To browse the tables/columns *within*
    this database, use :meth:`schema_rows`.

    Notes
    -----
    * Datasette caps arbitrary-SQL results at ``max_returned_rows`` (default
      1000); when a result is truncated the connection emits a ``UserWarning``.
      Add a ``LIMIT`` (or raise Datasette's ``max_returned_rows``) to control it.
    * Pass ``token=`` for an instance behind bearer-token auth.
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
        resp = self._client.get(
            f"{self._base_url}/{self._database}.json",
            params={"sql": sql, "_shape": "arrays"},
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return ``(columns, rows, types)`` for the shared cursor.

        SQLite query results carry no per-column types (dynamic typing), so
        ``types`` is None — DB-API type codes come out as None; column types are
        available via :meth:`schema_rows` instead.
        """
        data = self._run_sql(query)
        if data.get("truncated"):
            warnings.warn(
                "Datasette truncated the result set at max_returned_rows. "
                "Add a LIMIT to your query (or raise Datasette's "
                "max_returned_rows) to fetch the rest.",
                stacklevel=3,
            )
        return data.get("columns") or [], data.get("rows", []), None

    def schema_rows(self) -> list[dict[str, Any]]:
        """Return ``{"table", "column", "type"}`` rows for every user table.

        Raises ``ValueError`` if the response isn't the expected 3-column shape —
        fail early rather than hand back a malformed schema.
        """
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
        """List the databases served by this connection's Datasette instance.

        Discovery from a single connection: hits ``/-/databases.json`` with this
        connection's base URL, token, and pooled client, skipping the in-memory
        cross-database database. Pair with :meth:`for_database` to open one.
        See also the module-level :func:`databases`.
        """
        return databases(self._base_url, self._token, client=self._client)

    def for_database(self, database: str) -> "DatasetteConnection":
        """Open a new connection to another database on the same instance.

        Reuses this connection's base URL and token. Datasette scopes SQL per
        database, so a sibling database is a separate connection.
        """
        return DatasetteConnection(self._base_url, database, token=self._token)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def databases(
    base_url: str,
    token: str | None = None,
    *,
    client: httpx.Client | None = None,
) -> list[str]:
    """Return the database names a Datasette instance serves.

    Uses Datasette's documented ``/-/databases.json`` introspection endpoint
    (gated by the same permission as querying, so ``token`` flows through). The
    in-memory cross-database database (``_memory``) is skipped — it isn't a real
    dataset. Returns each database's ``route`` (the URL-safe name used in the
    query endpoint).
    """
    owns = client is None
    client = client or _require_httpx().Client(timeout=120)
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = client.get(f"{base_url.rstrip('/')}/-/databases.json", headers=headers)
        resp.raise_for_status()
        return [d["route"] for d in resp.json() if not d.get("is_memory")]
    finally:
        if owns:
            client.close()
