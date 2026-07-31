"""Tiny marimo connection adapter for :mod:`connectorx`."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

from ._dependencies import require_dependency
from .query import QueryConnection

_DIALECTS = {
    "bigquery": "bigquery",
    "clickhouse": "clickhouse",
    "mariadb": "mysql",
    "mssql": "tsql",
    "mysql": "mysql",
    "oracle": "oracle",
    "postgres": "postgres",
    "postgresql": "postgres",
    "redshift": "redshift",
    "sqlite": "sqlite",
}


def _infer_dialect(connection: Any) -> str | None:
    if isinstance(connection, str):
        return _DIALECTS.get(urlsplit(connection).scheme.lower())
    return None


class ConnectorXConnection(QueryConnection):
    """Run SQL through ``connectorx.read_sql`` with minimal syntax."""

    def __init__(
        self,
        connection: str | Mapping[str, str],
        *,
        dialect: str | None = None,
        return_type: str = "pandas",
        schema: Callable[[], list[dict[str, Any]]] | None = None,
        **read_sql_options: Any,
    ) -> None:
        resolved_dialect = dialect or _infer_dialect(connection)
        if resolved_dialect is None:
            raise ValueError(
                "dialect is required for federated or unrecognized connection URLs"
            )

        connectorx = require_dependency(
            "connectorx", connection_name="ConnectorXConnection"
        )
        if return_type == "pandas":
            require_dependency("pandas", connection_name="ConnectorXConnection")
        elif return_type == "polars":
            require_dependency("polars", connection_name="ConnectorXConnection")
        elif return_type in ("arrow", "arrow_stream"):
            require_dependency(
                "pyarrow",
                connection_name="ConnectorXConnection",
                package_name="pyarrow",
            )

        def query(sql: str) -> Any:
            result = connectorx.read_sql(
                connection,
                sql,
                return_type=return_type,
                **read_sql_options,
            )
            if return_type == "arrow_stream":
                read_all = getattr(result, "read_all", None)
                if not callable(read_all):
                    raise TypeError(
                        "ConnectorX return_type='arrow_stream' did not return "
                        "a PyArrow RecordBatchReader"
                    )
                return read_all()
            return result

        super().__init__(query, dialect=resolved_dialect, schema=schema)
