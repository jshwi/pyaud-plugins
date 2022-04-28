"""
pyaud_plugins._plugins.parametrize
==================================
"""
import typing as t

import pyaud


@pyaud.plugins.register()
class Doctest(pyaud.plugins.Parametrize):
    """Run ``doctest`` on all code examples."""

    def plugins(self) -> t.List[str]:
        return ["doctest-package", "doctest-readme"]


@pyaud.plugins.register()
class Files(pyaud.plugins.Parametrize):
    """Audit project data files.

    Make docs/<APPNAME>.rst, whitelist.py, and requirements.txt if none
    already exist, update them if they do and changes are needed or pass
    if nothing needs to be done.
    """

    def plugins(self) -> t.List[str]:
        return ["requirements", "toc", "whitelist"]


@pyaud.plugins.register()
class Test(pyaud.plugins.Parametrize):
    """Run all tests."""

    def plugins(self) -> t.List[str]:
        return ["doctest", "coverage"]
