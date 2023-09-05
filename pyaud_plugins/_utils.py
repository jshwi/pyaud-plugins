"""
pyaud_plugins._utils
====================
"""
from __future__ import annotations

import difflib
from pathlib import Path as _Path

import setuptools as _setuptools
import tomli
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter

# noinspection PyUnresolvedReferences
from pygments.lexers.diff import DiffLexer


def get_packages() -> list[str]:
    """Return list of Python package names currently in project.

    Prevent dot separated subdirectories (import syntax) as args are
    evaluated by path.

    Only return the parent package's name.

    :raises PythonPackageNotFoundError: Raised if no package can be
        found.
    :return: List of Python packages.
    """
    packages = list(
        {
            i.split(".", maxsplit=1)[0]
            for i in _setuptools.find_packages(
                # in response to an update to `setuptools` stubs:
                # - error: Argument "where" has incompatible type
                #   "Path"; expected "str"
                where=str(_Path.cwd()),
                exclude=["tests"],
            )
        }
    )
    return sorted(packages)


def package() -> str | None:
    """Return name of primary Python package.

    :raises PythonPackageNotFoundError: Raised if no primary package can
        be determined.
    :return: Name of primary Python package.
    """
    # at least one package will be returned or an error would have been
    # raised
    packages = get_packages()

    # if there is only one package then that is the default
    if len(packages) == 1:
        return packages.pop()

    # if there are multiple packages found then look for a configured
    # package name that matches one of the project's packages
    pyproject_toml = _Path.cwd() / "pyproject.toml"
    if pyproject_toml.is_file():
        config = tomli.loads(pyproject_toml.read_text(encoding="utf-8"))
        name = config.get("tool", {}).get("poetry", {}).get("name")
        if name is not None:
            name = name.replace("-", "_")
            if name in packages:
                return name

    # if there are multiple packages found, and none of the above two
    # apply, then the package with the same name as the project root (if
    # it exists) is the default
    repo = _Path.cwd().name
    if repo in packages:
        return repo

    return None


def print_diff(str1: str, str2: str) -> None:
    """Print diff with syntax highlighting.

    :param str1: String one.
    :param str2: String two.
    """
    differ = difflib.Differ()
    diff = differ.compare(str1.splitlines(), str2.splitlines())
    print(
        highlight(
            "\n".join(diff), DiffLexer(), Terminal256Formatter(style="monokai")
        )
    )
