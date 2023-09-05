"""
pyaud.parsers
=============
"""
from __future__ import annotations

from pathlib import Path as _Path
from types import TracebackType as _TracebackType


class LineSwitch:
    """Take the ``path`` and ``replace`` argument from the commandline.

    Reformat the README whilst returning the original title to the
    parent process.

    :param path: File to manipulate.
    :param obj: t.Dictionary of line number's as key and replacement
        strings as values.
    """

    def __init__(self, path: _Path, obj: dict[int, str]) -> None:
        self._path = path
        self.read = path.read_text(encoding="utf-8")
        edit = self.read.splitlines()
        for count, _ in enumerate(edit):
            if count in obj:
                edit[count] = obj[count]

        path.write_text("\n".join(edit), encoding="utf-8")

    def __enter__(self) -> LineSwitch:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: _TracebackType | None = None,
    ) -> bool:
        self._path.write_text(self.read, encoding="utf-8")
        return True
