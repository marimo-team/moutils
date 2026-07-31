"""Marimo SQL connection for the OpenSearch Python client."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._core import Connection
from ._dependencies import require_dependency

_SQL_PATH = "/_plugins/_sql"


class OpenSearchConnection(Connection):
    """Run OpenSearch SQL through an existing ``OpenSearch`` client."""

    dialect = "sql"

    def __init__(
        self,
        client: Any,
        *,
        fetch_size: int = 1_000,
        close_client: bool = False,
    ) -> None:
        require_dependency(
            "opensearchpy",
            connection_name="OpenSearchConnection",
            package_name="opensearch-py",
        )
        if isinstance(fetch_size, bool) or not isinstance(fetch_size, int):
            raise TypeError("fetch_size must be an integer")
        if fetch_size < 1:
            raise ValueError("fetch_size must be positive")
        self._client = client
        self._fetch_size = fetch_size
        self._close_client = close_client

    def _request(self, body: dict[str, Any], *, path: str = _SQL_PATH) -> Mapping:
        response = self._client.transport.perform_request("POST", path, body=body)
        response = getattr(response, "body", response)
        if not isinstance(response, Mapping):
            raise ValueError("unexpected OpenSearch response shape")
        return response

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        data = self._request({"query": query, "fetch_size": self._fetch_size})
        columns: list[Any] | None = None
        types: list[Any] | None = None
        rows: list[Any] = []
        cursor: str | None = None
        try:
            while True:
                if columns is None:
                    schema = data.get("schema")
                    if not isinstance(schema, list) or not all(
                        isinstance(column, Mapping) for column in schema
                    ):
                        raise ValueError("OpenSearch response has no schema")
                    columns = [column.get("name") for column in schema]
                    types = [column.get("type") for column in schema]
                page_rows = data.get("datarows", [])
                if not isinstance(page_rows, list):
                    raise ValueError("unexpected OpenSearch rows")
                rows.extend(page_rows)
                cursor = data.get("cursor")
                if not cursor:
                    break
                data = self._request({"cursor": cursor})
            return columns, rows, types
        finally:
            if cursor:
                try:
                    self._request({"cursor": cursor}, path=f"{_SQL_PATH}/close")
                except Exception:
                    pass  # Do not hide the query error with a cleanup failure.

    def close(self) -> None:
        if self._close_client:
            self._client.close()
