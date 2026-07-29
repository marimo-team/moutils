"""HTTP contract — verified with `responses` (real request-building, no network)."""

import json

import pytest
import requests
import responses

from moutils.db import PostHogConnection


@responses.activate
def test_execute_builds_request_and_parses():
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={
            "columns": ["date", "n"],
            "types": [["date", "Date"], ["n", "UInt64"]],
            "results": [["2026-01-01", 5]],
        },
    )
    cur = PostHogConnection(api_key="k", project_id=42).cursor().execute("SELECT 1")
    assert [d[0] for d in cur.description] == ["date", "n"]
    assert [d[1] for d in cur.description] == ["Date", "UInt64"]
    assert cur.fetchall() == [["2026-01-01", 5]]

    body = json.loads(responses.calls[0].request.body)
    assert body["query"] == {"kind": "HogQLQuery", "query": "SELECT 1"}
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer k"
    assert req.headers["Content-Type"] == "application/json"


@responses.activate
def test_int_project_id_in_url():
    responses.post(
        "https://us.posthog.com/api/projects/123/query/",
        json={"columns": [], "results": []},
    )
    PostHogConnection(api_key="k", project_id=123).cursor().execute("SELECT 1")
    assert (
        responses.calls[0].request.url
        == "https://us.posthog.com/api/projects/123/query/"
    )


@responses.activate
def test_host_trailing_slash_stripped():
    responses.post(
        "https://eu.posthog.com/api/projects/7/query/",
        json={"columns": [], "results": []},
    )
    conn = PostHogConnection(api_key="k", project_id=7, host="https://eu.posthog.com/")
    conn.cursor().execute("SELECT 1")
    url = responses.calls[0].request.url
    assert url == "https://eu.posthog.com/api/projects/7/query/"
    assert "//api" not in url


@responses.activate
@pytest.mark.parametrize("status", [401, 500])
def test_http_error_propagates(status):
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={"detail": "nope"},
        status=status,
    )
    with pytest.raises(requests.HTTPError):
        PostHogConnection(api_key="bad", project_id=42).cursor().execute("SELECT 1")


def test_commit_rollback_close_are_noops():
    conn = PostHogConnection(api_key="k", project_id=1)
    assert conn.commit() is None
    assert conn.rollback() is None
    assert conn.close() is None


def test_dialect_is_clickhouse():
    assert PostHogConnection(api_key="k", project_id=1).dialect == "clickhouse"
