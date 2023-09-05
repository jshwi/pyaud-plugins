"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
# pylint: disable=invalid-name,too-many-public-methods
from __future__ import annotations

from pathlib import Path as _Path

from environs import Env as _Env

from ._utils import package as _package


class _Environ(_Env):
    @property
    def PREFIX(self) -> str:
        """Prefix for variables which may turn out to be ambiguous."""
        return "PYAUD_"

    @property
    def WHITELIST(self) -> _Path:
        """File for allowed "unused" code (usually false-positives)."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "WHITELIST", default=_Path("whitelist.py")
            )

    @property
    def DOCS(self) -> _Path:
        """Location of the user's documentation."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path("DOCS", default=_Path("docs"))

    @property
    def BUILDDIR(self) -> _Path:
        """Where to put built documentation."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "BUILDDIR", default=self.DOCS / "_build"
            )

    @property
    def PACKAGE_TOC(self):
        """Location of the user's <PACKAGENAME>.toc."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PACKAGE_TOC", default=self.DOCS / f"{self.PACKAGE_NAME}.rst"
            )

    @property
    def DOCS_CONF(self) -> _Path:
        """Location of the user's documentation config."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "DOCS_CONF", default=self.DOCS / "conf.py"
            )

    @property
    def README_RST(self) -> _Path:
        """Location of the README.rst."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "README", default=_Path("README.rst")
            )

    @property
    def TESTS(self) -> _Path:
        """Location of tests."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path("TESTS", default=_Path("tests"))

    @property
    def PACKAGE(self) -> _Path:
        """Location of Python package."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PACKAGE", default=_Path.cwd() / self.PACKAGE_NAME
            )

    @property
    def PACKAGE_NAME(self) -> str:
        """Name of the package this is being run on."""
        with self.prefixed(self.PREFIX):
            return self.str("PACKAGE_NAME", default=_package())

    @property
    def PYPROJECT(self) -> _Path:
        """Location of pyproject.toml file."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PYPROJECT", default=_Path("pyproject.toml")
            )

    @property
    def ABOUT_TESTS(self):
        """Location of the about tests README."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "ABOUT_TESTS", default=self.TESTS / "TESTS.md"
            )

    @property
    def COMMIT_POLICY(self):
        """Location of the commit policy."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "ABOUT_TESTS", default=_Path(".github") / "COMMIT_POLICY.md"
            )


#: package environment, both parsed from .env file (with set defaults
#: for missing keys), and static values
environ = _Environ()
