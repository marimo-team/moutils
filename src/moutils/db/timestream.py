"""Marimo SQL connection for Amazon Timestream for LiveAnalytics."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from ._core import Connection
from ._dependencies import require_dependency

_SCHEMA_SQL = (
    'select table_name as "table", column_name as "column", '
    'data_type as "type" from information_schema.columns '
    "order by table_name, ordinal_position"
)


def _type_name(type_info: Mapping[str, Any]) -> str | None:
    scalar = type_info.get("ScalarType")
    if scalar:
        return str(scalar)
    if "ArrayColumnInfo" in type_info:
        nested = type_info["ArrayColumnInfo"]
        return f"ARRAY<{_type_name(nested.get('Type', {}))}>"
    if "TimeSeriesMeasureValueColumnInfo" in type_info:
        nested = type_info["TimeSeriesMeasureValueColumnInfo"]
        return f"TIMESERIES<{_type_name(nested.get('Type', {}))}>"
    if "RowColumnInfo" in type_info:
        fields = type_info["RowColumnInfo"]
        inner = ", ".join(
            f"{field.get('Name', '')} {_type_name(field.get('Type', {}))}"
            for field in fields
        )
        return f"ROW<{inner}>"
    return None


def _scalar(value: str, scalar_type: str | None) -> Any:
    if scalar_type == "BOOLEAN":
        return value.lower() == "true"
    if scalar_type == "BIGINT":
        return int(value)
    if scalar_type == "DOUBLE":
        return float(value)
    if scalar_type == "DECIMAL":
        return Decimal(value)
    return value


def _datum(data: Mapping[str, Any], column: Mapping[str, Any]) -> Any:
    if data.get("NullValue") is True:
        return None
    type_info = column.get("Type", {})
    if "ScalarValue" in data:
        return _scalar(data["ScalarValue"], type_info.get("ScalarType"))
    if "ArrayValue" in data:
        nested = type_info.get("ArrayColumnInfo", {})
        return [_datum(value, nested) for value in data["ArrayValue"]]
    if "RowValue" in data:
        fields = type_info.get("RowColumnInfo", [])
        values = data["RowValue"].get("Data", [])
        return {
            field.get("Name", str(index)): _datum(value, field)
            for index, (field, value) in enumerate(zip(fields, values))
        }
    if "TimeSeriesValue" in data:
        nested = type_info.get("TimeSeriesMeasureValueColumnInfo", {})
        return [
            {"time": point.get("Time"), "value": _datum(point["Value"], nested)}
            for point in data["TimeSeriesValue"]
        ]
    raise ValueError(f"unexpected Timestream datum: {data!r}")


class TimestreamConnection(Connection):
    """Run SQL through an existing boto3 ``timestream-query`` client."""

    dialect = "trino"

    def __init__(
        self,
        client: Any,
        *,
        page_size: int = 1_000,
        close_client: bool = False,
    ) -> None:
        require_dependency("boto3", connection_name="TimestreamConnection")
        if isinstance(page_size, bool) or not isinstance(page_size, int):
            raise TypeError("page_size must be an integer")
        if not 1 <= page_size <= 1_000:
            raise ValueError("page_size must be between 1 and 1,000")
        self._client = client
        self._page_size = page_size
        self._close_client = close_client

    def _fetch(self, query: str) -> tuple[list[Any], list[Any], Any]:
        request: dict[str, Any] = {
            "QueryString": query,
            "MaxRows": self._page_size,
        }
        columns: list[Any] | None = None
        types: list[Any] | None = None
        rows: list[Any] = []
        while True:
            response = self._client.query(**request)
            schema = response.get("ColumnInfo")
            if columns is None:
                if not isinstance(schema, list):
                    raise ValueError("Timestream response has no ColumnInfo")
                columns = [column.get("Name", "") for column in schema]
                types = [_type_name(column.get("Type", {})) for column in schema]
            if not isinstance(schema, list):
                schema = []
            page_rows = response.get("Rows", [])
            if not isinstance(page_rows, list):
                raise ValueError("unexpected Timestream rows")
            for row in page_rows:
                values = row.get("Data") if isinstance(row, Mapping) else None
                if not isinstance(values, list) or len(values) != len(schema):
                    raise ValueError("unexpected Timestream row shape")
                rows.append(
                    [_datum(value, column) for value, column in zip(values, schema)]
                )
            token = response.get("NextToken")
            if not token:
                break
            request["NextToken"] = token
        return columns, rows, types

    def schema_rows(self) -> list[dict[str, Any]]:
        columns, rows, _ = self._fetch(_SCHEMA_SQL)
        if columns != ["table", "column", "type"]:
            raise ValueError(f"unexpected Timestream schema columns: {columns!r}")
        return [
            {"table": str(table), "column": str(column), "type": str(type_)}
            for table, column, type_ in rows
        ]

    def close(self) -> None:
        if self._close_client:
            self._client.close()
