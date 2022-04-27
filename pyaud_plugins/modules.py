"""
pyaud_plugins.modules
=====================
"""
import os
import shutil
import sys
import tempfile
import typing as t
from pathlib import Path

import pyaud
from object_colors import Color

from ._abc import CheckFix, SphinxBuild
from ._environ import environ as e

colors = Color()
colors.populate_colors()


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
        """Confirm that a test suite exists.

        :return: Does a test suite exist? True or False.
        """
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
class Deploy(pyaud.plugins.Parametrize):
    """Deploy package documentation and test coverage."""

    def plugins(self) -> t.List[str]:
        return ["deploy-cov", "deploy-docs"]


@pyaud.plugins.register()
class DeployCov(pyaud.plugins.Action):
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet.

    If no ``CODECOV_TOKEN`` environment variable has been exported or
    defined in ``.env`` announce that no authorization token has been
    created yet.
    """

    codecov = "codecov"

    @property
    def exe(self) -> t.List[str]:
        return [self.codecov]

    def action(self, *args: str, **kwargs: bool) -> int:
        self.logger().debug("looking for %s", e.COVERAGE_XML)
        if not e.COVERAGE_XML.is_file():
            print("No coverage report found")
            return 0

        if e.CODECOV_TOKEN is None:
            print("CODECOV_TOKEN not set")
            return 0

        return self.subprocess[self.codecov].call(
            "--file", e.COVERAGE_XML, **kwargs
        )


@pyaud.plugins.register()
class DeployDocs(pyaud.plugins.Action):  # pyli
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch for
    tests).

    If the correct branch is the one in use deploy. ``gh-pages`` to the
    orphaned branch - otherwise do nothing and announce.
    """

    _pushing_skipped = "Pushing skipped"
    _origin = "origin"
    _gh_pages = "gh-pages"

    def deploy_docs(self) -> None:
        """Series of functions for deploying docs."""
        root_html = Path.cwd() / "html"
        pyaud.git.add(".")
        pyaud.git.diff_index("--cached", "HEAD", capture=True)
        stashed = False
        if pyaud.git.stdout():
            pyaud.git.stash(devnull=True)
            stashed = True

        shutil.move(str(e.DOCS_HTML), root_html)
        shutil.copy(e.README_RST, root_html / e.README_RST.name)
        pyaud.git.rev_list("--max-parents=0", "HEAD", capture=True)
        stdout = pyaud.git.stdout()
        if stdout:
            pyaud.git.checkout(stdout[-1])

        pyaud.git.checkout("--orphan", self._gh_pages)
        pyaud.git.config("--global", "user.name", e.GH_NAME)
        pyaud.git.config("--global", "user.email", e.GH_EMAIL)
        shutil.rmtree(e.DOCS)
        pyaud.git.rm("-rf", Path.cwd(), devnull=True)
        pyaud.git.clean("-fdx", "--exclude=html", devnull=True)
        for file in root_html.rglob("*"):
            shutil.move(str(file), Path.cwd() / file.name)

        shutil.rmtree(root_html)
        pyaud.git.add(".")
        pyaud.git.commit(
            "-m", '"[ci skip] Publishes updated documentation"', devnull=True
        )
        pyaud.git.remote("rm", self._origin)
        pyaud.git.remote("add", self._origin, e.GH_REMOTE)
        pyaud.git.fetch()
        pyaud.git.stdout()
        pyaud.git.ls_remote(
            "--heads", e.GH_REMOTE, self._gh_pages, capture=True
        )
        result = pyaud.git.stdout()
        remote_exists = None if not result else result[-1]
        pyaud.git.diff(
            self._gh_pages, "origin/gh-pages", suppress=True, capture=True
        )
        result = pyaud.git.stdout()
        remote_diff = None if not result else result[-1]
        if remote_exists is not None and remote_diff is None:
            colors.green.print("No difference between local branch and remote")
            print(self._pushing_skipped)
        else:
            colors.green.print("Pushing updated documentation")
            pyaud.git.push(self._origin, self._gh_pages, "-f")
            print("Documentation Successfully deployed")

        pyaud.git.checkout("master", devnull=True)
        if stashed:
            pyaud.git.stash("pop", devnull=True)

        pyaud.git.branch("-D", self._gh_pages, devnull=True)

    def action(self, *args: str, **kwargs: bool) -> int:
        if pyaud.branch() == "master":
            git_credentials = ["GH_NAME", "GH_EMAIL", "GH_TOKEN"]
            null_vals = [k for k in git_credentials if getattr(e, k) is None]
            if not null_vals:
                if not e.DOCS_HTML.is_dir():
                    pyaud.plugins.get("docs")(**kwargs)

                self.deploy_docs()
            else:
                print("The following is not set:")
                for null_val in null_vals:
                    print(f"- {e.PREFIX}{null_val}")

                print()
                print(self._pushing_skipped)
        else:
            colors.green.print("Documentation not for master")
            print(self._pushing_skipped)

        return 0


@pyaud.plugins.register()
class Docs(SphinxBuild):
    """Compile package documentation with ``Sphinx``.

    This is so the hyperlink isn't exactly the same as the package
    documentation.

    Build the ``Sphinx`` html documentation. Return the README's title
    to what it originally was.
    """

    @property
    def args(self) -> t.Tuple[t.Union[str, Path], ...]:
        return "-M", "html", e.DOCS, e.BUILDDIR, "-W"

    def action(self, *args: str, **kwargs: bool) -> int:
        pyaud.plugins.get("toc")(*args, **kwargs)
        shutil.rmtree(e.BUILDDIR, ignore_errors=True)
        with pyaud.parsers.Md2Rst(e.README_MD, temp=True):
            if not e.DOCS_CONF.is_file() or not e.README_RST.is_file():
                print("No docs found")
                return 0

            with pyaud.parsers.LineSwitch(
                e.README_RST,
                {0: e.README_RST.stem, 1: len(e.README_RST.stem) * "="},
            ):
                returncode = self.sphinx_build(*args, **kwargs)
                if not returncode:
                    colors.green.bold.print("Build successful")

        return returncode


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
class Lint(pyaud.plugins.Audit):
    """Lint code with ``pylint``."""

    pylint = "pylint"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pylint]

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

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
class Readme(pyaud.plugins.Action):
    """Parse, test, and assert RST code-blocks."""

    readmetester = "readmetester"

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    def exe(self) -> t.List[str]:
        return [self.readmetester]

    def action(self, *args: str, **kwargs: bool) -> int:
        if e.README_RST.is_file():
            self.subprocess[self.readmetester].call(
                e.README_RST, *args, **kwargs
            )
        else:
            print("No README.rst found in project root")

        return 0


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
class Const(pyaud.plugins.Audit):
    """Check code for repeat use of strings."""

    constcheck = "constcheck"
    cache = True
    cache_all = True

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    def exe(self) -> t.List[str]:
        return [self.constcheck]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.constcheck].call(*pyaud.files.args())


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

    @property
    def args(self) -> t.Tuple[t.Union[str, Path], ...]:
        return "-M", "doctest", e.DOCS, e.BUILDDIR


@pyaud.plugins.register()
class Doctest(pyaud.plugins.Parametrize):
    """Run ``doctest`` on all code examples."""

    def plugins(self) -> t.List[str]:
        return ["doctest-package", "doctest-readme"]


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


@pyaud.plugins.register()
class Test(pyaud.plugins.Parametrize):
    """Run all tests."""

    def plugins(self) -> t.List[str]:
        return ["doctest", "coverage"]
