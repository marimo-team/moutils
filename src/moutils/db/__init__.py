"""DB-API-compatible adapters for marimo SQL cells.

Import a connection from its submodule. Then assign it to a notebook variable:

    from moutils.db.posthog import PostHogConnection
    from moutils.db.datasette import DatasetteConnection
    from moutils.db.query import QueryConnection

    posthog = PostHogConnection(
        api_key="phx_...", project_id=123, page_size=10_000
    )
    datasette = DatasetteConnection("https://example.com", "mydb")
    custom = QueryConnection(my_query_function, dialect="sqlite")

Import provider adapters from their modules so optional SDKs stay optional.
"""
