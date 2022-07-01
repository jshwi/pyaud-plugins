"""
pyaud_plugins._plugins.fix
==========================
"""
from __future__ import annotations

import os
import typing as t

import pyaud

from pyaud_plugins._abc import CheckFix
from pyaud_plugins._environ import environ as e


@pyaud.plugins.register()
class Format(CheckFix):
    """Audit code with `Black`."""

    black = "black"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.black]

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
            *self.args,
            *pyaud.files.args(),
            *args,
            **kwargs,
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.flynt].call(
            *self.args, *pyaud.files.args(), *args, **kwargs
        )


@pyaud.plugins.register()
class FormatDocs(CheckFix):
    """Format docstrings with ``docformatter``."""

    docformatter = "docformatter"
    cache = True

    @property
    def args(self) -> t.Tuple[str | os.PathLike, ...]:
        return "--recursive", "--wrap-summaries", "72"

    @property
    def exe(self) -> t.List[str]:
        return [self.docformatter]
