import sys
from collections.abc import Callable, Iterable, Sized
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from typing import Optional, Type

if sys.version_info >= (3, 14):
    from concurrent.futures import InterpreterPoolExecutor


import marimo as mo


def concurrent_map[T, R](
    # Note: The `Executor`` abstract class does not specify arguments in __init__(), so
    # we specify a union of the individual types.
    pool: Type[ThreadPoolExecutor | ProcessPoolExecutor | "InterpreterPoolExecutor"],
    fn: Callable[[T], R],
    iterable: Iterable[T],
    *,
    total: Optional[int] = None,
    title: str | None = None,
    max_workers: Optional[int] = None,
    disabled: bool = False,
) -> list[R]:
    results = []
    if total is None:
        if isinstance(iterable, Sized):
            total = len(iterable)
        else:
            raise ValueError("total must be specified for non-sized iterables")
    try:
        with pool(max_workers=max_workers) as executor:
            futures = executor.map(fn, iterable)
            for future in mo.status.progress_bar(
                futures, total=total, title=title, disabled=disabled
            ):
                results.append(future)
    except KeyboardInterrupt:
        mo.stop(True, "Interrupted by user")
    return results


# This could also be done with functools.partial()
def thread_map[T, R](
    fn: Callable[[T], R],
    iterable: Iterable[T],
    *,
    total: Optional[int] = None,
    title: str | None = None,
    max_workers: Optional[int] = None,
    disabled: bool = False,
) -> list[R]:
    return concurrent_map(
        ThreadPoolExecutor,
        fn,
        iterable,
        total=total,
        title=title,
        max_workers=max_workers,
        disabled=disabled,
    )


def process_map[T, R](
    fn: Callable[[T], R],
    iterable: Iterable[T],
    *,
    total: Optional[int] = None,
    title: str | None = None,
    max_workers: Optional[int] = None,
    disabled: bool = False,
) -> list[R]:
    return concurrent_map(
        ProcessPoolExecutor,
        fn,
        iterable,
        total=total,
        title=title,
        max_workers=max_workers,
        disabled=disabled,
    )


if sys.version_info >= (3, 14):

    def interpreter_map[T, R](
        fn: Callable[[T], R],
        iterable: Iterable[T],
        *,
        total: Optional[int] = None,
        title: str | None = None,
        max_workers: Optional[int] = None,
        disabled: bool = False,
    ) -> list[R]:
        return concurrent_map(
            InterpreterPoolExecutor,
            fn,
            iterable,
            total=total,
            title=title,
            max_workers=max_workers,
            disabled=disabled,
        )
else:

    def interpreter_map(*args, **kwargs) -> list[None]:
        raise NotImplementedError(
            "InterpreterPoolExecutor is not available in Python < 3.14"
        )
