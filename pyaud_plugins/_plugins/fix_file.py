"""
pyaud_plugins._plugins.fix_file
===============================
"""
from __future__ import annotations

import os
import tempfile
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._environ import environ as e


@pyaud.plugins.register()
class Imports(pyaud.plugins.FixFile):
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` sorting imports. To avoid  running into false
    positives when running both in conjunction (as ``Black`` is
    uncompromising) run ``Black`` straight after.

    To effectively test this, for lack of stdin functionality, use
    ``tempfile.NamedTemporaryFunction`` to first evaluate contents
    from original file, then after ``isort``, then after ``Black``.

    If nothing has changed, even if ``isort`` has changed a file,
    then the imports are sorted enough for ``Black``'s standard.

    If there is a change raise ``PyAuditError`` if ``-f/--fix`` or
    ``-s/--suppress`` was not passed to the commandline.

    If ``-f/--fix`` was passed then replace the original file with
    the temp file's contents.
    """

    isort = "isort"
    black = "black"
    result = ""
    content = ""
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.isort, self.black]

    def audit(self, file: Path, **kwargs: bool) -> int:
        # collect original file's contents
        with open(file, encoding=e.ENCODING) as fin:
            self.content = fin.read()

        # write original file's contents to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with open(tmp.name, "w", encoding=e.ENCODING) as fout:
                fout.write(self.content)

        # run both ``isort`` and ``black`` on the temporary file,
        # leaving the original file untouched
        self.subprocess[self.isort].call(tmp.name, file=os.devnull, **kwargs)
        self.subprocess[self.black].call(
            tmp.name,
            "--line-length",
            "79",
            loglevel="debug",
            file=os.devnull,
            **kwargs,
        )

        # collect the results from the temporary file
        with open(tmp.name, encoding=e.ENCODING) as fin:
            self.result = fin.read()

        os.remove(tmp.name)
        return 0

    def fail_condition(self) -> bool | None:
        return self.result != self.content

    def fix(self, file: Path, **kwargs: bool) -> None:
        print(f"Fixed {file.relative_to(Path.cwd())}")

        # replace original file's contents with the temp file post
        # ``isort`` and ``Black``
        with open(file, "w", encoding=e.ENCODING) as fout:
            fout.write(self.result)
