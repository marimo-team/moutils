"""Schema discovery — DatabaseSchemaQuery parsing; fails early, no fallback."""

import json

import pytest
import requests
import responses

from moutils.db.posthog import (
    PostHogConnection,
    _rows_from_schema_response,
    schema_rows,
)


@responses.activate
def test_schema_rows_from_database_schema_query(schema_response):
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json=schema_response,
    )
    rows = schema_rows(PostHogConnection(api_key="k", project_id=42))

    # outbound body is the schema-query kind
    body = json.loads(responses.calls[0].request.body)
    assert body["query"] == {"kind": "DatabaseSchemaQuery"}

    assert {"table": "events", "column": "uuid", "type": "string"} in rows
    assert {"table": "events", "column": "properties", "type": "json"} in rows
    assert {"table": "persons", "column": "id", "type": "string"} in rows
    assert {r["table"] for r in rows} == {"events", "persons"}
    assert len(rows) == 6  # 4 event fields + 2 person fields


@responses.activate
def test_http_error_propagates():
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={"detail": "boom"},
        status=500,
    )
    with pytest.raises(requests.HTTPError):
        schema_rows(PostHogConnection(api_key="k", project_id=42))


@responses.activate
def test_garbage_shape_raises():
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={"unexpected": "shape"},
    )
    with pytest.raises(ValueError):
        schema_rows(PostHogConnection(api_key="k", project_id=42))


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"tables": {}},
        {"tables": {"events": "not-an-object"}},
        {"tables": {"events": {"name": "events"}}},  # no fields
        {"tables": {"events": {"fields": {}}}},  # empty fields -> no columns
    ],
)
def test_rows_from_schema_response_rejects(bad):
    with pytest.raises(ValueError):
        _rows_from_schema_response(bad)


def test_field_without_type_gives_none():
    data = {"tables": {"t": {"fields": {"c": {}}}}}
    rows = _rows_from_schema_response(data)
    assert rows == [{"table": "t", "column": "c", "type": None}]


@responses.activate
def test_connection_schema_rows_method(schema_response):
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json=schema_response,
    )
    rows = PostHogConnection(api_key="k", project_id=42).schema_rows()
    assert {r["table"] for r in rows} == {"events", "persons"}
    assert len(rows) == 6
