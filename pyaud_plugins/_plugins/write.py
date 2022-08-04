"""
pyaud_plugins._plugins.write
============================
"""
import os
import tempfile
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._environ import environ as e


@pyaud.plugins.register()
class Requirements(pyaud.plugins.Fix):
    """Audit requirements.txt with Pipfile.lock."""

    p2req = "pipfile2req"
    cache_file = e.REQUIREMENTS

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    @property
    def exe(self) -> t.List[str]:
        return [self.p2req]

    def audit(self, *args: str, **kwargs: bool) -> int:
        # get the stdout for both production and development packages
        if not e.PIPFILE_LOCK.is_file():
            return 0

        self.subprocess[self.p2req].call(
            e.PIPFILE_LOCK, *args, capture=True, **kwargs
        )
        self.subprocess[self.p2req].call(
            e.PIPFILE_LOCK, "--dev", *args, capture=True, **kwargs
        )

        # write to file and then use sed to remove the additional
        # information following the semicolon
        stdout = sorted(
            list(
                set(
                    "\n".join(
                        self.subprocess[self.p2req].stdout()
                    ).splitlines()
                )
            )
        )
        for content in stdout:
            self._content += f"{content.split(';')[0]}\n"

        if self.cache_file.is_file():
            return int(self.cache_file.read_text(e.ENCODING) != self._content)

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, e.ENCODING)
        return int(self.cache_file.read_text(e.ENCODING) != self._content)


@pyaud.plugins.register()
class Toc(pyaud.plugins.Fix):
    """Audit docs/<NAME>.rst toc-file."""

    sphinx_apidoc = "sphinx-apidoc"
    cache_file = e.PACKAGE_TOC

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    @property
    def exe(self) -> t.List[str]:
        return [self.sphinx_apidoc]

    def _read_temp(self, tempdir: Path) -> None:
        # dynamically populate a list of unwanted, overly nested files
        # nesting the file in the docs/<NAME>.rst file is preferred
        contents: t.List[str] = []
        tmpfile = tempdir / e.PACKAGE_TOC.name
        if tmpfile.is_file():
            contents.extend(tmpfile.read_text(e.ENCODING).splitlines())

        nested = [
            tempdir / f
            for f in tempdir.iterdir()
            if len(f.name.split(".")) > 2
        ]
        for file in nested:

            # extract the data from the nested toc
            contents.extend(file.read_text(e.ENCODING).splitlines())

        contents = sorted(
            [i for i in contents if i.startswith(".. automodule::")]
        )

        toc_attrs = "   :members:\n   :undoc-members:\n   :show-inheritance:"
        self._content = "{}\n{}\n\n".format(
            e.PACKAGE_NAME, len(e.PACKAGE_NAME) * "="
        )
        for content in contents:
            self._content += f"{content}\n{toc_attrs}\n"

    def audit(self, *args: str, **kwargs: bool) -> int:
        # write original file's contents to temporary file
        with tempfile.TemporaryDirectory() as tmp:
            tempdir = Path(tmp)
            self.subprocess[self.sphinx_apidoc].call(
                "-o",
                tempdir,
                e.PACKAGE,
                "-f",
                *args,
                file=os.devnull,
                **kwargs,
            )
            self._read_temp(tempdir)

        if self.cache_file.is_file():
            return int(self.cache_file.read_text(e.ENCODING) != self._content)

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, e.ENCODING)
        return int(self.cache_file.read_text(e.ENCODING) != self._content)


@pyaud.plugins.register()
class Whitelist(pyaud.plugins.Fix):
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.
    """

    vulture = "vulture"
    cache_file = e.WHITELIST

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    def audit(self, *args: str, **kwargs: bool) -> int:
        # append whitelist exceptions for each individual module
        kwargs["suppress"] = True
        self.subprocess[self.vulture].call(
            *pyaud.files.args(reduce=True),
            "--make-whitelist",
            *args,
            capture=True,
            **kwargs,
        )
        stdout = self.subprocess[self.vulture].stdout()
        stdout = sorted(
            [i.replace(str(Path.cwd()) + os.sep, "") for i in stdout]
        )
        self._content = "\n".join(stdout) + "\n"
        if self.cache_file.is_file():
            return int(self.cache_file.read_text(e.ENCODING) != self._content)

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, e.ENCODING)
        return int(self.cache_file.read_text(e.ENCODING) != self._content)


@pyaud.plugins.register()
class SortPyproject(pyaud.plugins.Fix):
    """Sort pyproject.toml file with ``toml-sort``."""

    toml_sort = "toml-sort"
    cache_file = e.PYPROJECT

    @property
    def exe(self) -> t.List[str]:
        return [self.toml_sort]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.toml_sort].call(
            e.PYPROJECT, "--check", *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.toml_sort].call(
            e.PYPROJECT, "--in-place", "--all", *args, **kwargs
        )
