"""
tests
=====

Test package for ``pyaud-plugins``.
"""
import re
import typing as t
from pathlib import Path

MockMainType = t.Callable[..., None]
MockFuncType = t.Callable[..., int]
MockCallStatusType = t.Callable[[str, int], MockFuncType]
MockSPOutputType = t.Callable[..., None]
MakeTreeType = t.Callable[[Path, t.Dict[str, t.Any]], None]
MockSPPrintCalledType = t.Callable[[], None]
MockSPCallNullType = t.Callable[[], None]


class MockSPCallType(t.Protocol):  # pylint: disable=too-few-public-methods
    """Type for ``fixture_patch_sp_call``"""

    def __call__(self, func: MockFuncType, returncode: int = ..., /) -> None:
        """Type for ``fixture_patch_sp_call``"""


FILE = "file.py"
GH_NAME = "test_user"
GH_EMAIL = "test_email.com"
TOKEN = "token"
INITIAL_COMMIT = "Initial commit"
NO_ISSUES = "Success: no issues found in 1 source files"
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
REQUIREMENTS = "requirements"
UNUSED = "unused"
WHITELIST = "whitelist"
SP_REPR_PYTEST = "<Subprocess (pytest)>"
COVERAGE = "coverage"
FORMAT = "format"
INIT_REMOTE = "init_remote"
TYPECHECK = "typecheck"
DEPLOY_COV = "deploy-cov"
FORMAT_DOCS = "format-docs"
TOC = "toc"
IMPORTS = "imports"
DEPLOY_DOCS = "deploy-docs"
LOGGING = "logging"
CONST = "const"
DOCTEST_README = "doctest-readme"
DOCTEST_PACKAGE = "doctest-package"
DOCTEST = "doctest"
TEST = "test"
DEPLOY = "deploy"
FILES = "files"
README = "readme"
TESTS = "tests"
MODULES_RST = "modules.rst"
TEST_FORMAT = "test-format"


class NoColorCapsys:
    """Capsys but with a regex to remove ANSI escape codes.

    Class is preferable for this as we can instantiate the instance
    as a fixture that also contains the same attributes as capsys

    We can make sure that the class is instantiated without executing
    capsys immediately thus losing control of what stdout and stderr
    we are to capture

    :param capsys: Capture and return stdout and stderr stream.
    """

    def __init__(self, capsys: t.Any) -> None:
        self.capsys = capsys

    @staticmethod
    def _regex(out: str) -> str:
        """Replace ANSI color codes with empty strings.

        Remove all escape codes. Preference is to test colored output
        this way as colored strings can be tricky and the effort in
        testing their validity really isn't worthwhile. It is also
        hard to  read expected strings when they contain the codes.

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
