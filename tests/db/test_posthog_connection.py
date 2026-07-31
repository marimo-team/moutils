"""Tests for the PostHog HTTP contract."""

import json

import pytest
import requests
import responses

from moutils.db.posthog import PostHogConnection


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
    cur = (
        PostHogConnection(api_key="k", project_id=42, page_size=1_000)
        .cursor()
        .execute("SELECT 1")
    )
    assert [d[0] for d in cur.description] == ["date", "n"]
    assert [d[1] for d in cur.description] == ["Date", "UInt64"]
    assert cur.fetchall() == [["2026-01-01", 5]]

    body = json.loads(responses.calls[0].request.body)
    assert body["query"] == {
        "kind": "HogQLQuery",
        "query": "SELECT * FROM (SELECT 1) AS moutils_page LIMIT 1000",
    }
    req = responses.calls[0].request
    assert req.headers["Authorization"] == "Bearer k"
    assert req.headers["Content-Type"] == "application/json"


@responses.activate
def test_int_project_id_in_url():
    responses.post(
        "https://us.posthog.com/api/projects/123/query/",
        json={"columns": [], "results": []},
    )
    PostHogConnection(api_key="k", project_id=123, page_size=1_000).cursor().execute(
        "SELECT 1"
    )
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
    conn = PostHogConnection(
        api_key="k",
        project_id=7,
        page_size=1_000,
        host="https://eu.posthog.com/",
    )
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
        PostHogConnection(
            api_key="bad", project_id=42, page_size=1_000
        ).cursor().execute("SELECT 1")


@responses.activate
def test_bad_query_shape_raises():
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={"columns": ["n"]},
    )
    with pytest.raises(ValueError, match="query response shape"):
        PostHogConnection(api_key="k", project_id=42, page_size=1_000).cursor().execute(
            "SELECT 1"
        )


@responses.activate
def test_page_size_caps_query_with_limit():
    responses.post(
        "https://us.posthog.com/api/projects/42/query/",
        json={"columns": [], "results": []},
    )
    PostHogConnection(api_key="k", project_id=42, page_size=500).cursor().execute(
        "SELECT * FROM events LIMIT 10;"
    )

    body = json.loads(responses.calls[0].request.body)
    assert body["query"]["query"] == (
        "SELECT * FROM (SELECT * FROM events LIMIT 10) AS moutils_page LIMIT 500"
    )


def test_page_size_is_required():
    with pytest.raises(TypeError, match="page_size"):
        PostHogConnection(api_key="k", project_id=42)  # type: ignore[call-arg]


@pytest.mark.parametrize("page_size", [True, 1.5, "100"])
def test_page_size_must_be_an_integer(page_size):
    with pytest.raises(TypeError, match="page_size must be an integer"):
        PostHogConnection(api_key="k", project_id=42, page_size=page_size)


@pytest.mark.parametrize("page_size", [-1, 0, 50_001])
def test_page_size_must_be_in_range(page_size):
    with pytest.raises(ValueError, match="page_size must be between 1 and 50,000"):
        PostHogConnection(api_key="k", project_id=42, page_size=page_size)


@pytest.mark.parametrize("page_size", [1, 50_000])
def test_page_size_accepts_boundaries(page_size):
    conn = PostHogConnection(api_key="k", project_id=42, page_size=page_size)
    assert conn._page_size == page_size


def test_commit_rollback_close_are_noops():
    conn = PostHogConnection(api_key="k", project_id=1, page_size=1_000)
    assert conn.commit() is None
    assert conn.rollback() is None
    assert conn.close() is None


def test_dialect_is_clickhouse():
    assert (
        PostHogConnection(api_key="k", project_id=1, page_size=1_000).dialect
        == "clickhouse"
    )
