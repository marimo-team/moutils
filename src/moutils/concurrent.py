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
    # Note: The `Executor` abstract base class does not specify arguments in __init__(),
    # so we specify a union of the individual types. Also, InterpreterPoolExecutor is
    # only available in Python 3.14+, so we use a string literal to avoid import errors
    # in older versions.
    pool: Type[ThreadPoolExecutor | ProcessPoolExecutor | "InterpreterPoolExecutor"],
    fn: Callable[[T], R],
    iterable: Iterable[T],
    *,
    total: Optional[int] = None,
    title: str | None = None,
    subtitle: str | None = None,
    max_workers: Optional[int] = None,
    remove_on_exit: bool = False,
    disabled: bool = False,
) -> list[R]:
    results = []
    try:
        with pool(max_workers=max_workers) as executor:
            futures = executor.map(fn, iterable)
            if disabled:
                results = list(futures)
            elif isinstance(iterable, Sized):
                if total is None:
                    total = len(iterable)
                results = list(
                    mo.status.progress_bar(
                        futures,
                        total=total,
                        title=title,
                        subtitle=subtitle,
                        remove_on_exit=remove_on_exit,
                    )
                )
            else:
                with mo.status.spinner(
                    title=title, subtitle=subtitle, remove_on_exit=remove_on_exit
                ):
                    results = list(futures)

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
    subtitle: str | None = None,
    max_workers: Optional[int] = None,
    remove_on_exit: bool = False,
    disabled: bool = False,
) -> list[R]:
    return concurrent_map(
        ThreadPoolExecutor,
        fn,
        iterable,
        total=total,
        title=title,
        subtitle=subtitle,
        max_workers=max_workers,
        remove_on_exit=remove_on_exit,
        disabled=disabled,
    )


def process_map[T, R](
    fn: Callable[[T], R],
    iterable: Iterable[T],
    *,
    total: Optional[int] = None,
    title: str | None = None,
    subtitle: str | None = None,
    max_workers: Optional[int] = None,
    remove_on_exit: bool = False,
    disabled: bool = False,
) -> list[R]:
    return concurrent_map(
        ProcessPoolExecutor,
        fn,
        iterable,
        total=total,
        title=title,
        subtitle=subtitle,
        max_workers=max_workers,
        remove_on_exit=remove_on_exit,
        disabled=disabled,
    )


if sys.version_info >= (3, 14):

    def interpreter_map[T, R](
        fn: Callable[[T], R],
        iterable: Iterable[T],
        *,
        total: Optional[int] = None,
        title: str | None = None,
        subtitle: str | None = None,
        max_workers: Optional[int] = None,
        remove_on_exit: bool = False,
        disabled: bool = False,
    ) -> list[R]:
        return concurrent_map(
            InterpreterPoolExecutor,
            fn,
            iterable,
            total=total,
            title=title,
            subtitle=subtitle,
            max_workers=max_workers,
            remove_on_exit=remove_on_exit,
            disabled=disabled,
        )
else:

    def interpreter_map(*args, **kwargs) -> list[None]:
        raise NotImplementedError(
            "InterpreterPoolExecutor is not available in Python < 3.14"
        )
