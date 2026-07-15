"""Tests for concurrent execution helpers."""

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import moutils.concurrent as concurrent_module
from moutils.concurrent import concurrent_map


class DummyExecutor:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def map(self, fn, iterable):
        return (fn(item) for item in iterable)


class MockStatus:
    def __init__(self):
        self.progress_bar_calls = []
        self.spinner_calls = []

    def progress_bar(self, iterable, **kwargs):
        self.progress_bar_calls.append(kwargs)
        return iterable

    @contextmanager
    def spinner(self, **kwargs):
        self.spinner_calls.append(kwargs)
        yield


@pytest.fixture
def mock_mo_status(monkeypatch: pytest.MonkeyPatch) -> MockStatus:
    status = MockStatus()
    fake_marimo = SimpleNamespace(
        status=status,
        stop=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(concurrent_module, "mo", fake_marimo)
    return status


def _double(value):
    return value * 2


class TestConcurrentMap:
    @pytest.mark.parametrize(
        "iterable_cls,total,expected_branch,expected_total",
        [
            (list, None, "progress_bar", 3),
            (iter, None, "spinner", None),
            (list, 10, "progress_bar", 10),
            (iter, 10, "progress_bar", 10),
        ],
    )
    def test_progress_bar_or_spinner(
        self,
        mock_mo_status: MockStatus,
        iterable_cls,
        total,
        expected_branch,
        expected_total,
    ):
        status = mock_mo_status

        iterable = iterable_cls([1, 2, 3])
        result = concurrent_map(
            DummyExecutor,  # type: ignore  # Because there is no PoolExecutor protocol
            _double,
            iterable,
            total=total,
        )

        assert result == [2, 4, 6]

        if expected_branch == "progress_bar":
            assert len(status.progress_bar_calls) == 1
            assert status.progress_bar_calls[0]["total"] == expected_total
            assert status.spinner_calls == []
        else:
            assert status.progress_bar_calls == []
            assert len(status.spinner_calls) == 1

    def test_use_iterable_length_when_total_is_missing(
        self, mock_mo_status: MockStatus
    ):
        status = mock_mo_status

        result = concurrent_map(
            DummyExecutor,  # type: ignore  # Because there is no PoolExecutor protocol
            fn=_double,
            iterable=[4, 5],
            total=None,
        )

        assert result == [8, 10]
        assert len(status.progress_bar_calls) == 1
        assert status.progress_bar_calls[0]["total"] == 2
        assert status.spinner_calls == []
