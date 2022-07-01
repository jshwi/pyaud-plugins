"""
pyaud_plugins._plugins.action
=============================
"""
from __future__ import annotations

import os
import shutil
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._abc import SphinxBuild
from pyaud_plugins._environ import environ as e
from pyaud_plugins._parsers import LineSwitch, Md2Rst
from pyaud_plugins._utils import colors


@pyaud.plugins.register()
class Tests(pyaud.plugins.Action):
    """Run the package unit-tests with ``pytest``."""

    pytest = "pytest"
    cache = True
    cache_all = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pytest]

    @property
    def is_tests(self) -> bool:
        """Confirm that a test suite exists."""
        return any(
            f
            for f in pyaud.files
            for p in ("test_*.py", "*_test.py")
            if f.match(p) and str(e.TESTS) in str(f)
        )

    def action(self, *args: str, **kwargs: bool) -> int:
        if self.is_tests:
            return self.subprocess[self.pytest].call(*args, **kwargs)

        print("No tests found")
        return 0


@pyaud.plugins.register()
class Coverage(Tests):
    """Run package unit-tests with ``pytest`` and ``coverage``."""

    coverage = "coverage"

    @property
    def exe(self) -> t.List[str]:
        return [self.pytest, self.coverage]

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = super().action(
            *[f"--cov={i}" for i in pyaud.files.reduce()], **kwargs
        )
        if self.is_tests and not returncode:
            kwargs["suppress"] = True
            return self.subprocess[self.coverage].call("xml", *args, **kwargs)

        print("No coverage to report")
        return returncode


@pyaud.plugins.register()
class Docs(SphinxBuild):
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation.

    Build the ``Sphinx`` html documentation. Return the README's title
    to what it originally was.
    """

    @property
    def args(self) -> t.Tuple[str | os.PathLike, ...]:
        return "-M", "html", e.DOCS, e.BUILDDIR, "-W"

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = 0
        pyaud.plugins.get("toc")(*args, **kwargs)
        shutil.rmtree(e.BUILDDIR, ignore_errors=True)
        with Md2Rst(e.README_MD, temp=True):
            if e.DOCS_CONF.is_file() and e.README_RST.is_file():
                with LineSwitch(
                    e.README_RST,
                    {0: e.README_RST.stem, 1: len(e.README_RST.stem) * "="},
                ):
                    returncode = self.sphinx_build(*args, **kwargs)

        return returncode


@pyaud.plugins.register()
class DoctestReadme(pyaud.plugins.Action):
    """Run ``doctest`` on Python code-blocks in README."""

    python = "python"

    @property
    def exe(self) -> t.List[str]:
        return [self.python]

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = self.subprocess[self.python].call(
            "-m", "doctest", e.README_RST
        )
        if not returncode:
            colors.green.bold.print(
                "Success: No issues found in {}".format(
                    e.README_RST.relative_to(Path.cwd())
                )
            )

        return returncode


@pyaud.plugins.register()
class DoctestPackage(SphinxBuild):
    """Run ``doctest`` on package."""

    cache = True

    @property
    def args(self) -> t.Tuple[str | os.PathLike, ...]:
        return "-M", "doctest", e.DOCS, e.BUILDDIR
