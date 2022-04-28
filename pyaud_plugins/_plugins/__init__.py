"""
pyaud_plugins._plugins
======================
"""
import os
import tempfile
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._abc import CheckFix, ColorAudit, SphinxBuild
from pyaud_plugins._environ import environ as e
from pyaud_plugins._utils import colors

from . import action, audit, deprecate, fix, parametrize


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


@pyaud.plugins.register()
class Imports(pyaud.plugins.FixFile):
    """Audit imports with ``isort``.

    ``Black`` and ``isort`` clash in some areas when it comes to
    ``Black`` sorting imports. To avoid  running into false
    positives when running both in conjunction (as ``Black`` is
    uncompromising) run ``Black`` straight after.

    To effectively test this, for lack of stdin functionality, use
    ``tempfile.NamedTemporaryFunction`` to first evaluate contents
    from original file, then after ``isort``, then after ``Black``.

    If nothing has changed, even if ``isort`` has changed a file,
    then the imports are sorted enough for ``Black``'s standard.

    If there is a change raise ``PyAuditError`` if ``-f/--fix`` or
    ``-s/--suppress`` was not passed to the commandline.

    If ``-f/--fix`` was passed then replace the original file with
    the temp file's contents.
    """

    isort = "isort"
    black = "black"
    result = ""
    content = ""
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.isort, self.black]

    def audit(self, file: Path, **kwargs: bool) -> int:
        # collect original file's contents
        with open(file, encoding=e.ENCODING) as fin:
            self.content = fin.read()

        # write original file's contents to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with open(tmp.name, "w", encoding=e.ENCODING) as fout:
                fout.write(self.content)

        # run both ``isort`` and ``black`` on the temporary file,
        # leaving the original file untouched
        self.subprocess[self.isort].call(tmp.name, devnull=True, **kwargs)
        self.subprocess[self.black].call(
            tmp.name,
            "--line-length",
            "79",
            loglevel="debug",
            devnull=True,
            **kwargs,
        )

        # collect the results from the temporary file
        with open(tmp.name, encoding=e.ENCODING) as fin:
            self.result = fin.read()

        os.remove(tmp.name)
        return 0

    def fail_condition(self) -> t.Optional[bool]:
        return self.result != self.content

    def fix(self, file: Path, **kwargs: bool) -> None:
        print(f"Fixed {file.relative_to(Path.cwd())}")

        # replace original file's contents with the temp file post
        # ``isort`` and ``Black``
        with open(file, "w", encoding=e.ENCODING) as fout:
            fout.write(self.result)
