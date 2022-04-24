"""
tests
=====

Test package for ``pyaud-plugins``.
"""
import re
import typing as t
from pathlib import Path

# noinspection PyPackageRequirements
import pyaud

MockMainType = t.Callable[..., None]
MockFuncType = t.Callable[..., int]
MockCallStatusType = t.Callable[[str, int], MockFuncType]
MockSPOutputType = t.Callable[..., None]
MakeTreeType = t.Callable[[Path, t.Dict[str, t.Any]], None]
MockSPPrintCalledType = t.Callable[[], None]


class MockSPCallType(t.Protocol):  # pylint: disable=too-few-public-methods
    """Type for ``fixture_patch_sp_call``"""

    def __call__(self, func: MockFuncType, returncode: int = ..., /) -> None:
        """Type for ``fixture_patch_sp_call``"""


REAL_REPO = Path(__file__).parent.parent
FILES = "file.py"
PUSHING_SKIPPED = "Pushing skipped"
REPO = "repo"
GH_NAME = "test_user"
GH_EMAIL = "test_email.com"
GH_TOKEN = "token"
INITIAL_COMMIT = "Initial commit"
NO_ISSUES = "Success: no issues found in 1 source files"
INIT = "__init__.py"
CONFPY = "conf.py"
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEBUG = LEVELS[0]
INFO = LEVELS[1]
WARNING = LEVELS[2]
ERROR = LEVELS[3]
CRITICAL = LEVELS[4]
PYAUD_MODULES = "pyaud.main.plugins"
SP_OPEN_PROC = "spall.Subprocess._open_process"
README = Path("README.rst")
PYAUD_PLUGINS_PLUGINS = "pyaud.plugins._plugins"
TYPE_ERROR = "can only register one of the following:"
DOCS = Path("docs")
PIPFILE_LOCK = Path("Pipfile.lock")
RCFILE = f".{pyaud.__name__}rc"
TOMLFILE = f"{pyaud.__name__}.toml"
PYPROJECT = "pyproject.toml"
GITIGNORE = ".gitignore"
PYAUD_FILES_POPULATE = "pyaud.files.populate"
SP_CALL = "spall.Subprocess.call"
SP_STDOUT = "spall.Subprocess.stdout"
OS_GETCWD = "os.getcwd"
WHITELIST_PY = "whitelist.py"
COMMIT = "7c57dc943941566f47b9e7ee3208245d0bcd7656"


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
        return tuple(  # pylint: disable=consider-using-generator
            [self._regex(r) for r in self.capsys.readouterr()]
        )

    def stdout(self) -> str:
        """Return stdout without referencing the tuple indices.

        :return: Stdout.
        """
        return self.readouterr()[0]

    def stderr(self) -> str:
        """Return stderr without referencing the tuple indices.

        :return: Stderr.
        """
        return self.readouterr()[1]


class MockPluginType(pyaud.plugins.Plugin):
    """PluginType object."""


class MockCachedPluginType(MockPluginType):
    """PluginType object with ``cache`` set to True."""

    cache = True
