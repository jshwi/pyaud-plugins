"""
pyaud_plugins._plugins.action
=============================
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from subprocess import CalledProcessError

import git
import pyaud
import rich

from pyaud_plugins._environ import environ as e
from pyaud_plugins._parsers import LineSwitch


@pyaud.plugins.register()
class Tests(pyaud.plugins.Action):
    """Run the package unit-tests with ``pytest``."""

    cache = True
    cache_all = True

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
            return subprocess.run(["pytest", *args], check=True).returncode

        print("No tests found")
        return 0


@pyaud.plugins.register()
class Coverage(Tests):
    """Run package unit-tests with ``pytest`` and ``coverage``."""

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = super().action(
            *[f"--cov={i}" for i in pyaud.files.reduce()], **kwargs
        )
        if self.is_tests and not returncode:
            return subprocess.run(["coverage", "xml"], check=False).returncode

        print("No coverage to report")
        return returncode


@pyaud.plugins.register()
class Docs(pyaud.plugins.Action):
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation.

    Build the ``Sphinx`` html documentation. Return the README's title
    to what it originally was.
    """

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = 0
        pyaud.plugins.get("toc")(*args, **kwargs)
        shutil.rmtree(e.BUILDDIR, ignore_errors=True)
        if e.DOCS_CONF.is_file() and e.README_RST.is_file():
            with LineSwitch(
                e.README_RST,
                {0: e.README_RST.stem, 1: len(e.README_RST.stem) * "="},
            ):
                returncode = subprocess.run(
                    ["sphinx-build", "-M", "html", e.DOCS, e.BUILDDIR, "-W"],
                    check=True,
                ).returncode

        return returncode


@pyaud.plugins.register()
class DoctestReadme(pyaud.plugins.Action):
    """Run ``doctest`` on Python code-blocks in README."""

    def action(self, *args: str, **kwargs: bool) -> int:
        returncode = subprocess.run(
            ["python", "-m", "doctest", e.README_RST], check=False
        ).returncode
        if not returncode:
            rich.print(
                (
                    "[bold green]Success: No issues found in {}[/bold green]"
                ).format(e.README_RST.relative_to(Path.cwd()))
            )

        return 0 if os.name == "nt" else returncode


@pyaud.plugins.register()
class DoctestPackage(pyaud.plugins.Action):
    """Run ``doctest`` on package."""

    cache = True

    def action(self, *args: str, **kwargs: bool) -> int:
        return (
            0
            if os.name == "nt"
            else subprocess.run(
                ["sphinx-build", "-M", "doctest", e.DOCS, e.BUILDDIR],
                check=True,
            ).returncode
        )


@pyaud.plugins.register()
class ChangeLogged(pyaud.plugins.Action):
    """Check commits with loggable tags are added to CHANGELOG."""

    cache = False
    cache_all = False

    def action(self, *args: str, **kwargs: bool) -> int:
        loggable = {
            "Added": "add",
            "Changed": "change",
            "Deprecated": "deprecate",
            "Removed": "remove",
            "Fixed": "fix",
            "Security": "security",
        }
        repo = git.Repo(Path.cwd())
        for key, value in loggable.items():
            message = str(repo.head.commit.message).splitlines()[0]
            diff = repo.git.diff("HEAD^", "CHANGELOG.md")
            if message.startswith(value) and key not in diff:
                if not diff:
                    raise CalledProcessError(
                        1, "CHANGELOG has not been updated"
                    )

                raise CalledProcessError(
                    1, "CHANGELOG not updated with correct type"
                )

        return 0
