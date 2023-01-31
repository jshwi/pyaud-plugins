"""
pyaud_plugins._plugins.write
============================
"""
import os
import re
import tempfile
import typing as t
from pathlib import Path

import pyaud
import yaml

from pyaud_plugins._environ import environ as e

BANNER = """\
<!--
This file is auto-generated and any changes made to it will be overwritten
-->
"""


@pyaud.plugins.register()
class Requirements(pyaud.plugins.Fix):
    """Audit requirements.txt with Pipfile.lock.

    :param name: Name of plugin.
    """

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
    """Audit docs/<NAME>.rst toc-file.

    :param name: Name of plugin.
    """

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
            i for i in contents if i.startswith(".. automodule::")
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

    :param name: Name of plugin.
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
            i.replace(str(Path.cwd()) + os.sep, "") for i in stdout
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


@pyaud.plugins.register()
class AboutTests(pyaud.plugins.Fix):
    """Check tests README is up-to-date.

    :param name: Name of this plugin.
    """

    TEST_RST = """
tests
=====

.. automodule:: tests._test
    :members:
    :undoc-members:
    :show-inheritance:
"""

    sphinx_build = "sphinx-build"
    cache_file = Path("tests") / "TESTS.md"

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    @property
    def exe(self) -> t.List[str]:
        return [self.sphinx_build]

    def audit(self, *args: str, **kwargs: bool) -> int:
        self._content = BANNER
        docs = Path.cwd() / "docs"
        builddir = docs / "_build"
        tests_rst = docs / "tests.rst"
        unformatted_md = builddir / "markdown" / "tests.md"
        tests_rst.write_text(self.TEST_RST)
        self.subprocess[self.sphinx_build].call(
            "-M", "markdown", docs, builddir, file=os.devnull, *args, **kwargs
        )
        tests_rst.unlink()
        lines = unformatted_md.read_text(encoding="utf-8").splitlines()
        skip_lines = False
        for line in lines:
            match = re.match(r"(.*)tests\._test\.test_(.*)\((.*)", line)
            if match:
                skip_lines = False
                self._content += "{}{}\n\n".format(
                    match.group(1),
                    match.group(2).capitalize().replace("_", " "),
                )
            elif line.startswith("* **"):
                skip_lines = True
            elif not skip_lines:
                self._content += f"{line}\n"

        if self.cache_file.is_file():
            return int(
                self.cache_file.read_text(encoding="utf-8") != self._content
            )

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, encoding="utf-8")
        return int(
            self.cache_file.read_text(encoding="utf-8") != self._content
        )


@pyaud.plugins.register()
class CommitPolicy(pyaud.plugins.Fix):
    """Test commit policy is up to date.

    :param name: Name of this plugin.
    """

    cache_file = Path(".github") / "COMMIT_POLICY.md"

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    def audit(self, *args: str, **kwargs: bool) -> int:
        conform_yaml = Path.cwd() / ".conform.yaml"
        if not conform_yaml.is_file():
            return 0

        self._content = BANNER
        self._content += "# Commit Policy\n\n"
        commit_policy = {}
        for policy in yaml.safe_load(conform_yaml.read_text(encoding="utf-8"))[
            "policies"
        ]:
            if policy["type"] == "commit":
                commit_policy.update(policy["spec"])

        for header, obj in commit_policy.items():
            self._content += f"## {header.capitalize()}\n\n"
            if not isinstance(obj, dict):
                self._content += f"{obj}\n\n"
            else:
                for key, value in obj.items():
                    if isinstance(value, (bool, int, str)):
                        match = [
                            i for i in re.split("([A-Z][^A-Z]*)", key) if i
                        ]
                        if match:
                            key = " ".join(match).capitalize()
                        value = f"{key}: {value}"
                    else:
                        if isinstance(value, list):
                            value = "### {}\n\n- {}".format(
                                key.capitalize(), "\n- ".join(value)
                            )
                    self._content += f"{value}\n\n"

        if self.cache_file.is_file():
            return int(
                self.cache_file.read_text(encoding="utf-8") != self._content
            )

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, encoding="utf-8")
        return int(
            self.cache_file.read_text(encoding="utf-8") != self._content
        )
