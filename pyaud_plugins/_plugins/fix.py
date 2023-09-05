"""
pyaud_plugins._plugins.fix
==========================
"""
from __future__ import annotations

import typing as t

import pyaud

from pyaud_plugins._environ import environ as e

CHECK = "--check"


@pyaud.plugins.register()
class Format(pyaud.plugins.FixAll):
    """Audit code with `Black`."""

    black = "black"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.black]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            CHECK, *pyaud.files.args(), *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.black].call(
            *args, *pyaud.files.args(), **kwargs
        )


@pyaud.plugins.register()
class Unused(pyaud.plugins.FixAll):
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.
    """

    vulture = "vulture"

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    def audit(self, *args: str, **kwargs: bool) -> int:
        args = tuple([*pyaud.files.args(reduce=True), *args])
        if e.WHITELIST.is_file():
            args = str(e.WHITELIST), *args

        return self.subprocess[self.vulture].call(*args, **kwargs)

    def fix(self, *args: str, **kwargs: bool) -> int:
        pyaud.plugins.get("whitelist")(*args, **kwargs)
        return self.audit(*args, **kwargs)


@pyaud.plugins.register()
class FormatStr(pyaud.plugins.FixAll):
    """Format f-strings with ``flynt``."""

    flynt = "flynt"
    args = "--line-length", "79", "--transform-concats"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.flynt]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.flynt].call(
            "--dry-run",
            "--fail-on-change",
            *pyaud.files.args(),
            *self.args,
            *args,
            **kwargs,
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.flynt].call(
            *self.args, *pyaud.files.args(), *args, **kwargs
        )


@pyaud.plugins.register()
class FormatDocs(pyaud.plugins.FixAll):
    """Format docstrings with ``docformatter``."""

    docformatter = "docformatter"
    cache = True

    args = "--recursive", "--wrap-summaries", "72"

    @property
    def exe(self) -> t.List[str]:
        return [self.docformatter]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            CHECK, *pyaud.files.args(), *self.args, *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        returncode = self.subprocess[self.exe[0]].call(
            "--in-place",
            *pyaud.files.args(),
            *self.args,
            *args,
            **kwargs,
            suppress=True,
        )
        if returncode == 3:
            # in place for docformatter now returns 3, so this will
            # always fail without bringing back to 0
            returncode = 0

        return returncode


@pyaud.plugins.register()
class Imports(pyaud.plugins.FixAll):
    """Audit imports with ``isort``."""

    isort = "isort"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.isort]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            CHECK, *pyaud.files.args(), *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.isort].call(
            *pyaud.files.args(), *args, **kwargs
        )
