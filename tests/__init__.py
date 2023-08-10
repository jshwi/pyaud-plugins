"""
tests
=====

Test package for ``pyaud-plugins``.
"""
import contextlib
import re
import shutil
import typing as t
from pathlib import Path

from gitspy import Git
from mypy_extensions import KwArg
from templatest.utils import VarSeq

MockMainType = t.Callable[..., int]
MockFuncType = t.Callable[..., int]
MockCallStatusType = t.Callable[[str, int], MockFuncType]
MakeTreeType = t.Callable[
    [t.Union[str, Path], t.Dict[t.Union[str, Path], t.Any]], None
]
MockSPPrintCalledType = t.Callable[[], None]
MockSPCallNullType = t.Callable[[], None]
FixtureMockTemporaryDirectory = t.Callable[..., None]


class MockSPCallType(t.Protocol):  # pylint: disable=too-few-public-methods
    """Type for ``fixture_patch_sp_call``"""

    def __call__(self, func: MockFuncType, returncode: int = ..., /) -> None:
        """Type for ``fixture_patch_sp_call``"""


PACKAGE = VarSeq("package")

FILE = "file.py"
NO_ISSUES = "Success: no issues found in file"
NO_ISSUES_ALL = "Success: no issues found in 1 source files"
DEBUG = "DEBUG"
SP_OPEN_PROC = "spall.Subprocess._open_process"
PYAUD_PLUGINS_PLUGINS = "pyaud.plugins._plugins"
PYAUD_FILES_POPULATE = "pyaud.files.populate"
SP_CALL = "spall.Subprocess.call"
SP_STDOUT = "spall.Subprocess.stdout"
FLAG_SUPPRESS = "--suppress"
FLAG_FIX = "--fix"
NO_TESTS_FOUND = "No tests found"
FORMAT_STR = "format-str"
UNUSED = "unused"
WHITELIST = "whitelist"
SP_REPR_PYTEST = "<Subprocess (pytest)>"
COVERAGE = "coverage"
FORMAT = "format"
TYPECHECK = "typecheck"
FORMAT_DOCS = "format-docs"
TOC = "toc"
IMPORTS = "imports"
LOGGING = "logging"
CONST = "const"
DOCTEST_README = "doctest-readme"
DOCTEST_PACKAGE = "doctest-package"
DOCTEST = "doctest"
TEST = "test"
FILES = "files"
README = "readme"
TESTS = "tests"
TEST_FORMAT = "test-format"
CHANGE = "change"
TOOL = "tool"
INIT = "__init__.py"
REPO = "package"
GIT = "git"
README_HELP_CACHE_FILE = "pyaud_plugins._plugins.write.ReadmeHelp.cache_file"
README_HELP = "readme-help"


git = Git()

FixtureMockRepo = t.Callable[[KwArg(t.Callable[..., t.Any])], None]


class NoColorCapsys:
    """Capsys but with a regex to remove ANSI escape codes.

    Class is preferable for this as we can instantiate the instance as a
    fixture that also contains the same attributes as capsys

    We can make sure that the class is instantiated without executing
    capsys immediately thus losing control of what stdout and stderr we
    are to capture

    :param capsys: Capture and return stdout and stderr stream.
    """

    def __init__(self, capsys: t.Any) -> None:
        self.capsys = capsys

    @staticmethod
    def _regex(out: str) -> str:
        """Replace ANSI color codes with empty strings.

        Remove all escape codes. Preference is to test colored output
        this way as colored strings can be tricky and the effort in
        testing their validity really isn't worthwhile. It is also hard
        to  read expected strings when they contain the codes.

        :param out: String to strip of ANSI escape codes
        :return: Same string but without ANSI codes
        """
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", out)

    def readouterr(self) -> t.Tuple[str, ...]:
        """Call as capsys ``readouterr`` but remove ANSI color-codes.

        :return: A tuple (just like the capsys) containing stdout in the
            first index and stderr in the second
        """
        return tuple(self._regex(r) for r in self.capsys.readouterr())

    def stdout(self) -> str:
        """Return stdout without referencing the tuple indices.

        :return: Stdout.
        """
        return self.readouterr()[0]


class MockTemporaryDirectory:  # pylint: disable=too-few-public-methods
    """Mock ``tempfile.TemporaryDirectory``.

    :param temp_dirs: Paths to mock ``tempfile.TemporaryDirectory``
        with.
    """

    def __init__(self, *temp_dirs: Path) -> None:
        self._temp_dirs = list(temp_dirs)

    @contextlib.contextmanager
    def open(self) -> t.Generator[str, None, None]:
        """Mock dir returned from ``TemporaryDirectory`` constructor.

        :return: Generator yielding self.
        """
        temp_dir = self._temp_dirs.pop(0)
        temp_dir.mkdir()
        yield str(temp_dir)
        shutil.rmtree(temp_dir)
