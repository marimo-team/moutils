"""Shared DB-API 2.0 machinery for the moutils database connectors.

marimo detects any object exposing the DB-API surface (``cursor``/``commit``/
``rollback``/``close`` + an executable cursor) as a SQL engine, so assigning an
instance to a notebook variable makes the source available in SQL cells. The
class attr ``dialect`` tells marimo which SQL flavour to parse.

The cursor knows nothing about any particular data source: ``execute`` delegates
to the owning connection's ``_fetch(query) -> (columns, rows, types)`` and builds
the DB-API ``description`` from that triple. All paging/fetch state lives here, so
a connector only has to implement transport + result-mapping.

Subclasses must set ``dialect`` and implement:

    _fetch(query) -> (columns, rows, types | None)   # used by the cursor
    schema_rows() -> list[{"table", "column", "type"}]  # schema discovery
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence


class Cursor:
    """Minimal DB-API 2.0 cursor backed by a connection's ``_fetch``."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self.arraysize = 1
        self.description: Any = None
        self.rowcount: int = -1
        self.lastrowid = None
        self._rows: list[list[Any]] = []
        self._pos = 0

    def execute(self, query: str, parameters: Sequence[Any] | None = None) -> "Cursor":
        # Parameter binding isn't implemented; reject it loudly rather than
        # silently ignoring `parameters`.
        if parameters:
            raise NotImplementedError(
                "moutils.db cursors do not support parameter binding; "
                "interpolate values into the SQL query string yourself."
            )
        columns, rows, types = self._connection._fetch(query)
        # `types`, when present, is a list of [name, type] pairs (HogQL) or bare
        # type strings; connectors with no per-column types return None.
        if not types:
            types = [None] * len(columns)
        self._rows = [list(row) for row in rows]
        self._pos = 0
        self.rowcount = len(self._rows)
        # DB-API description: (name, type_code, display_size, internal_size,
        # precision, scale, null_ok)
        self.description = [
            (
                str(name),
                (t[1] if isinstance(t, (list, tuple)) and len(t) > 1 else t),
                None,
                None,
                None,
                None,
                None,
            )
            for name, t in zip(columns, types)
        ]
        return self

    def fetchall(self) -> list[list[Any]]:
        rest = self._rows[self._pos :]
        self._pos = len(self._rows)
        return rest

    def fetchone(self) -> list[Any] | None:
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchmany(self, size: int | None = None) -> list[list[Any]]:
        size = self.arraysize if size is None else size
        chunk = self._rows[self._pos : self._pos + size]
        self._pos += len(chunk)
        return chunk

    def close(self) -> None:
        self._rows = []
        self._pos = 0


class Connection(ABC):
    """DB-API 2.0 connection base for read-only REST-backed data sources.

    Abstract: a subclass must set ``dialect`` and implement the ``_fetch`` and
    ``schema_rows`` hooks below, so an incomplete connector fails at instantiation
    rather than at query time.
    """

    dialect: str = ""

    def cursor(self) -> Cursor:
        return Cursor(self)

    def commit(self) -> None:  # no-op: moutils.db connectors are read-only
        pass

    def rollback(self) -> None:  # no-op: moutils.db connectors are read-only
        pass

    def close(self) -> None:
        pass

    # --- hooks a connector must provide -------------------------------------
    @abstractmethod
    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return ``(columns, rows, types | None)`` for the shared cursor."""

    @abstractmethod
    def schema_rows(self) -> list[dict[str, Any]]:
        """Return ``{"table", "column", "type"}`` rows describing the schema."""
