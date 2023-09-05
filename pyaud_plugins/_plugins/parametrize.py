"""
pyaud_plugins._plugins.parametrize
==================================
"""
from __future__ import annotations

import pyaud


@pyaud.plugins.register()
class Doctest(pyaud.plugins.Parametrize):
    """Run ``doctest`` on all code examples."""

    def plugins(self) -> list[str]:
        return ["doctest-package", "doctest-readme"]


@pyaud.plugins.register()
class Files(pyaud.plugins.Parametrize):
    """Audit project data files.

    Make docs/<APPNAME>.rst, whitelist.py, and requirements.txt if none
    already exist, update them if they do and changes are needed or pass
    if nothing needs to be done.
    """

    def plugins(self) -> list[str]:
        return ["toc", "whitelist"]


@pyaud.plugins.register()
class Test(pyaud.plugins.Parametrize):
    """Run all tests."""

    def plugins(self) -> list[str]:
        return ["doctest", "coverage"]
