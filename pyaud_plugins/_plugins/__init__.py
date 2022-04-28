"""
pyaud_plugins._plugins
======================
"""
import os
import sys
import tempfile
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._abc import CheckFix, ColorAudit, SphinxBuild
from pyaud_plugins._environ import environ as e
from pyaud_plugins._utils import colors

from . import action, deprecate, parametrize


@pyaud.plugins.register()
class Format(CheckFix):
    """Audit code with `Black`."""

    black = "black"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.black]

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.black].call(
            *args, *pyaud.files.args(), **kwargs
        )


@pyaud.plugins.register()
class Lint(ColorAudit):
    """Lint code with ``pylint``."""

    pylint = "pylint"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pylint]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.pylint].call(
            "--output-format=colorized", *args, *pyaud.files.args(), **kwargs
        )


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
class Typecheck(pyaud.plugins.Audit):
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their stub-
    files.
    """

    mypy = "mypy"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.mypy]

    def audit(self, *args: str, **kwargs: bool) -> int:
        # save the value of ``suppress`` if it exists: default to False
        suppress = kwargs.get("suppress", False)

        # ignore the first error that might occur
        # capture output to analyse for missing stub libraries
        kwargs["suppress"] = True
        returncode = self.subprocess[self.mypy].call(
            "--ignore-missing-imports",
            *pyaud.files.args(),
            *args,
            capture=True,
            **kwargs,
        )

        # restore value of ``suppress``
        kwargs["suppress"] = suppress
        stdout = self.subprocess[self.mypy].stdout()

        # if no error occurred, continue on to print message and return
        # value
        if returncode:
            # if error occurred it might be because the stub library is
            # not installed: automatically download and install stub
            # library if the below message occurred
            if any(
                "error: Library stubs not installed for" in i for i in stdout
            ):
                self.subprocess[self.mypy].call(
                    "--non-interactive", "--install-types"
                )

                # continue on to run the first command again, which will
                # not, by default, ignore any consecutive errors
                # do not capture output again
                return self.subprocess[self.mypy].call(
                    "--ignore-missing-imports",
                    *pyaud.files.args(),
                    *args,
                    **kwargs,
                )

            # if any error occurred that wasn't because of a missing
            # stub library
            print("\n".join(stdout))
            if not suppress:
                raise pyaud.exceptions.AuditError(" ".join(sys.argv))

        else:
            print("\n".join(stdout))

        return returncode


@pyaud.plugins.register()
class Unused(pyaud.plugins.Fix):
    """Audit unused code with ``vulture``.

    Create whitelist first with --fix.
    """

    vulture = "vulture"

    @property
    def exe(self) -> t.List[str]:
        return [self.vulture]

    def audit(self, *args: str, **kwargs: bool) -> int:
        args = tuple([*pyaud.files.args(reduce=True), *args])
        if e.WHITELIST.is_file():
            args = str(e.WHITELIST), *args

        return self.subprocess[self.vulture].call(*args, **kwargs)

    def fix(self, *args: str, **kwargs: bool) -> int:
        pyaud.plugins.get("whitelist")(*args, **kwargs)
        return self.audit(*args, **kwargs)


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


@pyaud.plugins.register()
class FormatStr(pyaud.plugins.Fix):
    """Format f-strings with ``flynt``."""

    flynt = "flynt"
    args = "--line-length", "79", "--transform-concats"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.flynt]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.flynt].call(
            "--dry-run",
            "--fail-on-change",
            *self.args,
            *pyaud.files.args(),
            *args,
            **kwargs,
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.flynt].call(
            *self.args, *pyaud.files.args(), *args, **kwargs
        )


@pyaud.plugins.register()
class FormatDocs(CheckFix):
    """Format docstrings with ``docformatter``."""

    docformatter = "docformatter"
    cache = True

    @property
    def args(self) -> t.Tuple[t.Union[str, Path], ...]:
        return "--recursive", "--wrap-summaries", "72"

    @property
    def exe(self) -> t.List[str]:
        return [self.docformatter]


@pyaud.plugins.register()
class Const(ColorAudit):
    """Check code for repeat use of strings."""

    constcheck = "constcheck"
    cache = True
    cache_all = True

    @property
    def exe(self) -> t.List[str]:
        return [self.constcheck]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.constcheck].call(*pyaud.files.args())


@pyaud.plugins.register()
class SortPyproject(pyaud.plugins.Fix):
    """Sort pyproject.toml file with ``toml-sort``."""

    toml_sort = "toml-sort"

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
