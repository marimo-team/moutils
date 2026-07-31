"""Read-only REST connections for marimo SQL cells.

Import a connection from its submodule. Then assign it to a notebook variable:

    from moutils.db.posthog import PostHogConnection
    from moutils.db.datasette import DatasetteConnection

    posthog = PostHogConnection(
        api_key="phx_...", project_id=123, page_size=10_000
    )
    datasette = DatasetteConnection("https://example.com", "mydb")

PostHog uses ``requests``. Datasette requires the ``db`` optional dependency.
"""
