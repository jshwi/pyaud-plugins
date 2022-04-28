"""
pyaud_plugins._plugins
======================
"""
import os
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._abc import CheckFix, ColorAudit, SphinxBuild
from pyaud_plugins._environ import environ as e
from pyaud_plugins._utils import colors

from . import action, audit, deprecate, fix, fix_file, parametrize


@pyaud.plugins.register()
class Requirements(pyaud.plugins.Write):
    """Audit requirements.txt with Pipfile.lock."""

    p2req = "pipfile2req"

    @property
    def exe(self) -> t.List[str]:
        return [self.p2req]

    @property
    def path(self) -> Path:
        return e.REQUIREMENTS

    def required(self) -> Path:
        return e.PIPFILE_LOCK

    def write(self, *args: str, **kwargs: bool) -> int:
        # get the stdout for both production and development packages
        self.subprocess[self.p2req].call(
            self.required(), *args, capture=True, **kwargs
        )
        self.subprocess[self.p2req].call(
            self.required(), "--dev", *args, capture=True, **kwargs
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
        with open(self.path, "w", encoding=e.ENCODING) as fout:
            for content in stdout:
                fout.write(f"{content.split(';')[0]}\n")

        return 0


@pyaud.plugins.register()
class Toc(pyaud.plugins.Write):
    """Audit docs/<NAME>.rst toc-file."""

    sphinx_apidoc = "sphinx-apidoc"

    @property
    def exe(self) -> t.List[str]:
        return [self.sphinx_apidoc]

    @property
    def path(self) -> Path:
        return e.PACKAGE_TOC

    def required(self) -> t.Optional[Path]:
        return e.DOCS_CONF

    @staticmethod
    def _populate(path: Path, contents: t.List[str]) -> None:
        if path.is_file():
            with open(path, encoding=e.ENCODING) as fin:
                contents.extend(fin.read().splitlines())

    def write(self, *args: str, **kwargs: bool) -> int:
        toc_attrs = "   :members:\n   :undoc-members:\n   :show-inheritance:"
        self.subprocess[self.sphinx_apidoc].call(
            "-o", e.DOCS, e.PACKAGE, "-f", *args, devnull=True, **kwargs
        )

        # dynamically populate a list of unwanted, overly nested files
        # nesting the file in the docs/<NAME>.rst file is preferred
        nested = [
            e.DOCS / f for f in e.DOCS.iterdir() if len(f.name.split(".")) > 2
        ]

        contents: t.List[str] = []
        self._populate(self.path, contents)
        for file in nested:

            # extract the data from the nested toc
            self._populate(file, contents)

        contents = sorted(
            [i for i in contents if i.startswith(".. automodule::")]
        )
        with open(self.path, "w", encoding="utf-8") as fout:
            fout.write(
                "{}\n{}\n\n".format(e.PACKAGE_NAME, len(e.PACKAGE_NAME) * "=")
            )
            for content in contents:
                fout.write(f"{content}\n{toc_attrs}\n")

        # files that we do not want included in docs modules creates an
        # extra layer that is not desired for this module
        blacklist = [e.DOCS / "modules.rst", *nested]

        # remove unwanted files
        for module in blacklist:
            if module.is_file():
                os.remove(module)

        return 0


@pyaud.plugins.register()
class Whitelist(pyaud.plugins.Write):
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.
    """

    vulture = "vulture"

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    @property
    def path(self) -> Path:
        return e.WHITELIST

    def write(self, *args: str, **kwargs: bool) -> int:
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
        stdout = [i.replace(str(Path.cwd()) + os.sep, "") for i in stdout]
        stdout.sort()
        with open(self.path, "w", encoding=e.ENCODING) as fout:
            fout.write("\n".join(stdout) + "\n")

        return 0
