"""
pyaud_plugins._plugins.fix
==========================
"""
from __future__ import annotations

import subprocess

import pyaud

from pyaud_plugins._environ import environ as e

CHECK = "--check"


@pyaud.plugins.register()
class Format(pyaud.plugins.FixAll):
    """Audit code with `Black`."""

    cache = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["black", CHECK, *pyaud.files.args()], check=True
        ).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["black", *pyaud.files.args()], check=True
        ).returncode


@pyaud.plugins.register()
class Unused(pyaud.plugins.FixAll):
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.
    """

    def audit(self, *args: str, **kwargs: bool) -> int:
        _args = [*pyaud.files.args(reduce=True)]
        if e.WHITELIST.is_file():
            _args.insert(0, str(e.WHITELIST))

        return subprocess.run(["vulture", *_args], check=True).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        pyaud.plugins.get("whitelist")(*args, **kwargs)
        return self.audit(**kwargs)


@pyaud.plugins.register()
class FormatStr(pyaud.plugins.FixAll):
    """Format f-strings with ``flynt``."""

    args = "--line-length", "79", "--transform-concats"
    cache = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            [
                "flynt",
                "--dry-run",
                "--fail-on-change",
                *pyaud.files.args(),
                *self.args,
            ],
            check=True,
        ).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["flynt", *self.args, *pyaud.files.args()], check=True
        ).returncode


@pyaud.plugins.register()
class FormatDocs(pyaud.plugins.FixAll):
    """Format docstrings with ``docformatter``."""

    cache = True

    args = "--recursive", "--wrap-summaries", "72"

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["docformatter", CHECK, *pyaud.files.args(), *self.args],
            check=True,
        ).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        returncode = subprocess.run(
            ["docformatter", "--in-place", *pyaud.files.args(), *self.args],
            check=False,
        ).returncode
        if returncode == 3:
            # in place for docformatter now returns 3, so this will
            # always fail without bringing back to 0
            returncode = 0

        return returncode


@pyaud.plugins.register()
class Imports(pyaud.plugins.FixAll):
    """Audit imports with ``isort``."""

    cache = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["isort", CHECK, *pyaud.files.args()], check=True
        ).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["isort", *pyaud.files.args()], check=True
        ).returncode
