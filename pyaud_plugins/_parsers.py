"""
pyaud.parsers
=============
"""
from __future__ import annotations

import typing as _t
from pathlib import Path as _Path

from ._environ import environ as _e


class LineSwitch:
    """Take the ``path`` and ``replace`` argument from the commandline.

    Reformat the README whilst returning the original title to the
    parent process.

    :param path: File to manipulate.
    :param obj: t.Dictionary of line number's as key and replacement
        strings as values.
    """

    def __init__(self, path: _Path, obj: _t.Dict[int, str]) -> None:
        self._path = path
        self.read = path.read_text(encoding=_e.ENCODING)
        edit = self.read.splitlines()
        for count, _ in enumerate(edit):
            if count in obj:
                edit[count] = obj[count]

        path.write_text("\n".join(edit), encoding=_e.ENCODING)

    def __enter__(self) -> LineSwitch:
        return self

    def __exit__(
        self, exc_type: _t.Any, exc_val: _t.Any, exc_tb: _t.Any
    ) -> None:
        self._path.write_text(self.read, encoding=_e.ENCODING)
