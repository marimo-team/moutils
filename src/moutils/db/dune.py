"""Marimo SQL connection for the Dune API Python client."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from ._core import Connection
from ._dependencies import require_dependency

_TERMINAL_STATES = {
    "QUERY_STATE_CANCELLED",
    "QUERY_STATE_COMPLETED",
    "QUERY_STATE_COMPLETED_PARTIAL",
    "QUERY_STATE_EXPIRED",
    "QUERY_STATE_FAILED",
}
_SUCCESS_STATES = {"QUERY_STATE_COMPLETED", "QUERY_STATE_COMPLETED_PARTIAL"}


def _state_value(state: Any) -> str:
    return str(getattr(state, "value", state))


class DuneConnection(Connection):
    """Execute raw DuneSQL through an existing ``DuneClient``."""

    dialect = "trino"

    def __init__(
        self,
        client: Any,
        *,
        performance: str | None = None,
        poll_interval: float = 1,
        timeout: float | None = None,
        batch_size: int = 32_000,
    ) -> None:
        require_dependency(
            "dune_client",
            connection_name="DuneConnection",
            package_name="dune-client",
        )
        if poll_interval < 0:
            raise ValueError("poll_interval cannot be negative")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int):
            raise TypeError("batch_size must be an integer")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self._client = client
        self._performance = performance
        self._poll_interval = poll_interval
        self._timeout = timeout
        self._batch_size = batch_size

    def _wait(self, execution_id: str) -> None:
        deadline = None if self._timeout is None else time.monotonic() + self._timeout
        while True:
            status = self._client.get_execution_status(execution_id)
            state = _state_value(status.state)
            if state in _TERMINAL_STATES:
                if state not in _SUCCESS_STATES:
                    error = getattr(status, "error", None)
                    message = getattr(error, "message", None) or state
                    raise RuntimeError(f"Dune query failed: {message}")
                return
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError(f"Dune query {execution_id} timed out")
            time.sleep(self._poll_interval)

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        execution = self._client.execute_sql(
            query_sql=query,
            performance=self._performance,
        )
        execution_id = execution.execution_id
        self._wait(execution_id)

        offset = 0
        columns: list[Any] | None = None
        types: list[Any] | None = None
        rows: list[Any] = []
        while True:
            response = self._client.get_execution_results(
                execution_id,
                limit=self._batch_size,
                offset=offset,
            )
            result = response.result
            if result is None:
                raise ValueError("Dune completed without a result")
            metadata = result.metadata
            if columns is None:
                columns = list(metadata.column_names)
                types = list(metadata.column_types)
            for record in result.rows:
                if not isinstance(record, Mapping):
                    raise ValueError("unexpected Dune row shape")
                rows.append([record.get(column) for column in columns])
            next_offset = response.next_offset
            if next_offset is None:
                break
            offset = next_offset
        return columns, rows, types
