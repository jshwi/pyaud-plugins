"""
pyaud_plugins._plugins.write
============================
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pyaud
import yaml

from pyaud_plugins._environ import environ as e
from pyaud_plugins._utils import print_diff

BANNER = """\
<!--
This file is auto-generated and any changes made to it will be overwritten
-->
"""


@pyaud.plugins.register()
class Toc(pyaud.plugins.Fix):
    """Audit docs/<NAME>.rst toc-file.

    :param name: Name of plugin.
    """

    cache_file = e.PACKAGE_TOC

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    def _read_temp(self, tempdir: Path) -> None:
        # dynamically populate a list of unwanted, overly nested files
        # nesting the file in the docs/<NAME>.rst file is preferred
        contents: list[str] = []
        tmpfile = tempdir / e.PACKAGE_TOC.name
        if tmpfile.is_file():
            contents.extend(tmpfile.read_text("utf-8").splitlines())

        nested = [
            tempdir / f
            for f in tempdir.iterdir()
            if len(f.name.split(".")) > 2
        ]
        for file in nested:
            # extract the data from the nested toc
            contents.extend(file.read_text("utf-8").splitlines())

        contents = sorted(
            i for i in contents if i.startswith(".. automodule::")
        )

        toc_attrs = "   :members:\n   :undoc-members:\n   :show-inheritance:"
        self._content = f"{e.PACKAGE_NAME}\n{len(e.PACKAGE_NAME) * '='}\n\n"
        for content in contents:
            self._content += f"{content}\n{toc_attrs}\n"

    def audit(self, *args: str, **kwargs: bool) -> int:
        # write original file's contents to temporary file
        with tempfile.TemporaryDirectory() as tmp:
            tempdir = Path(tmp)
            subprocess.run(
                ["sphinx-apidoc", "-o", tempdir, e.PACKAGE, "-f"], check=True
            )
            self._read_temp(tempdir)

        if self.cache_file.is_file():
            return int(self.cache_file.read_text("utf-8") != self._content)

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, "utf-8")
        return int(self.cache_file.read_text("utf-8") != self._content)


@pyaud.plugins.register()
class Whitelist(pyaud.plugins.Fix):
    """Check whitelist.py file with ``vulture``.

    This will consider all unused code an exception so resolve code that
    is not to be excluded from the ``vulture`` search first.

    :param name: Name of plugin.
    """

    cache_file = e.WHITELIST

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""
        self._iswindows = os.name == "nt"

    def _file_status(self) -> int:
        equals = int(self.cache_file.read_text("utf-8") != self._content)
        return 0 if self._iswindows else equals

    @staticmethod
    def _do_format(i):
        obj, comment = i.replace(str(Path.cwd()) + os.sep, "").split("#")
        part1 = comment.split(":")[0].strip()
        return f"{obj}# {part1})"

    def audit(self, *args: str, **kwargs: bool) -> int:
        # append whitelist exceptions for each individual module
        result = subprocess.run(
            ["vulture", *pyaud.files.args(reduce=True), "--make-whitelist"],
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = sorted(self._do_format(i) for i in result.stdout.splitlines())
        self._content = "\n".join(stdout)
        self._content += "\n"
        if self.cache_file.is_file():
            return self._file_status()

        return 1

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(self._content, "utf-8")
        return self._file_status()


@pyaud.plugins.register()
class SortPyproject(pyaud.plugins.Fix):
    """Sort pyproject.toml file with ``toml-sort``."""

    cache_file = e.PYPROJECT

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["toml-sort", e.PYPROJECT, "--check"], check=True
        ).returncode

    def fix(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["toml-sort", e.PYPROJECT, "--in-place", "--all"], check=True
        ).returncode


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

    cache_file = Path("tests") / "TESTS.md"

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._content = ""

    def audit(self, *args: str, **kwargs: bool) -> int:
        sphinx_build = "sphinx-build"
        self._content = BANNER
        docs = Path.cwd() / "docs"
        readme = Path.cwd() / "README.rst"
        with TemporaryDirectory() as tmpdir:
            tmp_docs = Path(tmpdir) / "docs"
            shutil.copytree(docs, tmp_docs)
            if readme.is_file():
                shutil.copy(readme, tmp_docs.parent)

            builddir = tmp_docs / "_build"
            unformatted_md = builddir / "markdown" / "tests.md"
            tests_rst = tmp_docs / "tests.rst"
            tests_rst.write_text(self.TEST_RST)
            subprocess.run(
                [sphinx_build, "-M", "markdown", tmp_docs, builddir],
                check=True,
            )
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


@pyaud.plugins.register()
class ReadmeHelp(pyaud.plugins.Fix):
    """Test help documented in README is up to date.

    :param name: Name of this plugin.
    """

    cache_file = Path("README.rst")
    tab = "    "

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.readme_content = ""
        self.current_help = ""
        self.readme_help = ""

    def _get_help_in_readme(self) -> tuple[int, int, str]:
        self.readme_content = self.cache_file.read_text(encoding="utf-8")
        argparse_tokens = [
            "usage",
            "[-h]",
            "optional arguments:",
            "-h, --help",
            "show this help message and exit",
        ]
        in_code_block = False
        lines: list[str] = []
        dedent = False
        start = 0
        for count, line in enumerate(self.readme_content.splitlines()):
            if ".. code-block:: console" in line:
                start = count
                dedent = False
                in_code_block = True

            if in_code_block:
                lines.append(line)
                if line == "":
                    dedent = True

                elif dedent:
                    if line.startswith(self.tab):
                        dedent = False
                    else:
                        string = "\n".join(lines)
                        if all(i in string for i in argparse_tokens):
                            return start, count - 1, string

                        lines = []
                        dedent = False
                        in_code_block = False

        return 0, 0, ""

    def audit(self, *args: str, **kwargs: bool) -> int:
        if self.cache_file.is_file():
            os.environ.update({"COLUMNS": "100", "LINES": "24"})
            start, end, string = self._get_help_in_readme()
            if not string:
                return 0

            executable = string.splitlines()[2].split()[1]
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            self.current_help = ansi_escape.sub(
                "",
                "\n".join(
                    f"{self.tab}{i}" if i != "" else ""
                    for i in subprocess.run(
                        [executable, "--help"], capture_output=True, check=True
                    )
                    .stdout.decode()
                    .splitlines()
                ),
            ).replace(
                # in 3.10 `argparse.ArgumentParser` changes
                # `optional arguments` to simply `options`, which will
                # yield inconsistent results in programs built for
                # multiple versions without this
                "options:",
                "optional arguments:",
            )
            start = start + 2
            self.readme_help = "\n".join(
                self.readme_content.splitlines()[start:end]
            )
            returncode = int(self.current_help != self.readme_help)
            if returncode:
                print_diff(self.current_help, self.readme_help)
                return returncode

        return 0

    def fix(self, *args: str, **kwargs: bool) -> int:
        self.cache_file.write_text(
            self.readme_content.replace(self.readme_help, self.current_help),
            encoding="utf-8",
        )
        return 0
