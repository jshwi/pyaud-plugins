"""
pyaud.environ
=============

Set up the environment variables for the current project.
"""
# pylint: disable=invalid-name,too-many-public-methods
from __future__ import annotations

from pathlib import Path as _Path

import pyaud as _pyaud
from environs import Env as _Env


class _Environ(_Env):
    @property
    def PREFIX(self) -> str:
        """Prefix for variables which may turn out to be ambiguous."""
        return "PYAUD_"

    @property
    def REPO(self) -> str:
        """The name of the repo that this is being run in."""
        return _Path.cwd().name

    @property
    def GITHUB_REPOSITORY_OWNER(self) -> str | None:
        """Env variable which may exist in a GitHub workflow."""
        return self.str("GITHUB_REPOSITORY_OWNER", default=None)

    @property
    def WHITELIST(self) -> _Path:
        """File for allowed "unused" code (usually false-positives)."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "WHITELIST", default=_Path("whitelist.py")
            )

    @property
    def COVERAGE_XML(self) -> _Path:
        """Location to store coverage.xml file."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "COVERAGE_XML", default=_Path("coverage.xml")
            )

    @property
    def REQUIREMENTS(self) -> _Path:
        """Where to find requirements.txt (or other named) file."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "REQUIREMENTS", default=_Path("requirements.txt")
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
    def GH_NAME(self) -> str | None:
        """Username of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_NAME", default=self.GITHUB_REPOSITORY_OWNER)

    @property
    def GH_EMAIL(self) -> str | None:
        """Email of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_EMAIL", default=None)

    @property
    def GH_TOKEN(self) -> str | None:
        """Authentication token of GH user."""
        with self.prefixed(self.PREFIX):
            return self.str("GH_TOKEN", default=None)

    @property
    def CODECOV_TOKEN(self) -> str | None:
        """Authentication token for codecov.io."""
        return self.str("CODECOV_TOKEN", default=None)

    @property
    def GH_REMOTE(self) -> str | None:
        """URL of repository remote."""
        default = None
        if all([self.GH_NAME, self.GH_EMAIL, self.GH_TOKEN]):
            default = "https://{0}:{1}@github.com/{0}/{2}.git".format(
                self.GH_NAME, self.GH_TOKEN, self.REPO
            )

        with self.prefixed(self.PREFIX):
            return self.str("GH_REMOTE", default=default)

    @property
    def ENCODING(self) -> str:
        """Default encoding."""
        with self.prefixed(self.PREFIX):
            return self.str("ENCODING", default="utf-8")

    @property
    def PIPFILE_LOCK(self) -> _Path:
        """Location of the user's Pipfile.lock."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PIPFILE_LOCK", default=_Path("Pipfile.lock")
            )

    @property
    def PACKAGE_TOC(self):
        """Location of the user's <PACKAGENAME>.toc."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PACKAGE_TOC", default=self.DOCS / f"{self.PACKAGE_NAME}.rst"
            )

    @property
    def DOCS_HTML(self) -> _Path:
        """Location of the user's html docs."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "DOCS_HTML", default=self.BUILDDIR / "html"
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
    def README_MD(self) -> _Path:
        """Location of the README.md."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "README", default=_Path("README.md")
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
            return self.str("PACKAGE_NAME", default=_pyaud.package())

    @property
    def PYPROJECT(self) -> _Path:
        """Location of pyproject.toml file."""
        with self.prefixed(self.PREFIX):
            return _Path.cwd() / self.path(
                "PYPROJECT", default=_Path("pyproject.toml")
            )


#: package environment, both parsed from .env file (with set defaults
#: for missing keys), and static values
environ = _Environ()
