"""Shared DB-API-compatible classes for marimo query adapters."""

from abc import ABC, abstractmethod
from typing import Any, Sequence


def _type_code(types: list[Any], index: int) -> Any:
    if index >= len(types):
        return None
    type_ = types[index]
    if isinstance(type_, (list, tuple)) and len(type_) > 1:
        return type_[1]
    return type_


class Cursor:
    """A minimal DB-API-compatible cursor."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self.arraysize = 1
        self.description: Any = None
        self.rowcount: int = -1
        self.lastrowid = None
        self._rows: list[list[Any]] = []
        self._pos = 0

    def execute(self, query: str, parameters: Sequence[Any] | None = None) -> "Cursor":
        # marimo passes an empty tuple when a query has no parameters.
        if parameters:
            raise NotImplementedError(
                "moutils.db cursors do not support bound parameters. "
                "Pass a query without parameters."
            )
        columns, rows, types = self._connection._fetch(query)
        types = list(types or ())
        self._rows = [list(row) for row in rows]
        self._pos = 0
        self.rowcount = len(self._rows)
        # DB-API description: (name, type_code, display_size, internal_size,
        # precision, scale, null_ok)
        self.description = [
            (
                str(name),
                _type_code(types, index),
                None,
                None,
                None,
                None,
                None,
            )
            for index, name in enumerate(columns)
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
    """Base class for marimo-compatible query connections."""

    dialect: str = ""

    def cursor(self) -> Cursor:
        return Cursor(self)

    def commit(self) -> None:  # no-op: adapters do not manage transactions
        pass

    def rollback(self) -> None:  # no-op: adapters do not manage transactions
        pass

    def close(self) -> None:
        pass

    @abstractmethod
    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        """Return ``(columns, rows, types | None)`` for the shared cursor."""

    def schema_rows(self) -> list[dict[str, Any]]:
        """Return ``{"table", "column", "type"}`` rows describing the schema.

        Schema discovery is optional because marimo's generic DB-API engine does
        not currently consume it. Connections with a cheap metadata endpoint can
        override this method for callers that want to inspect the source directly.
        """
        return []
