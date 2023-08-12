"""
tests.conftest
==============
"""
# pylint: disable=protected-access,no-member,too-many-statements
from __future__ import annotations

import os
import typing as t
from configparser import ConfigParser
from pathlib import Path

import pyaud
import pytest
import setuptools
from mypy_extensions import KwArg, VarArg

# noinspection PyUnresolvedReferences,PyProtectedMember
from pyaud import _objects as pc
from pyaud.__main__ import main

from . import (
    FixtureMockRepo,
    FixtureMockTemporaryDirectory,
    MakeTreeType,
    MockCallStatusType,
    MockFuncType,
    MockMainType,
    MockSPCallNullType,
    MockSPCallType,
    MockSPPrintCalledType,
    MockTemporaryDirectory,
    NoColorCapsys,
    git,
)

MOCK_PACKAGE = "package"

original_setuptools_find_packages = setuptools.find_packages


@pytest.fixture(name="mock_environment", autouse=True)
def fixture_mock_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_repo: FixtureMockRepo
) -> None:
    """Mock imports to reflect the temporary testing environment.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    :param mock_repo: Mock ``git.Repo`` class.
    """
    # set environment variables
    # =========================
    # load generic env variables so as to avoid a KeyError and override
    # relevant variables for test environment
    monkeypatch.setenv("HOME", str(tmp_path))

    # load plugins dir
    # ================
    pyaud.plugins.load()

    # patch 3rd party attributes
    # ==========================
    # set the cwd to the temporary project dir
    # ensure no real .env file interferes with tests
    # patch ``setuptools.find_package`` to return package as existing
    monkeypatch.setattr("os.getcwd", lambda: str(tmp_path / MOCK_PACKAGE))
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path / MOCK_PACKAGE)
    monkeypatch.setattr(
        "setuptools.find_packages", lambda *_, **__: [MOCK_PACKAGE]
    )

    # mock path resolutions for `environs` module
    # prevent lookup of .env file in this repo's real dir
    current_frame = type("current_frame", (), {})
    current_frame.f_back = type("f_back", (), {})  # type: ignore
    current_frame.f_back.f_code = type("f_code", (), {})  # type: ignore
    current_frame.f_back.f_code.co_filename = str(  # type: ignore
        Path.cwd() / "_main.py"
    )
    monkeypatch.setattr("inspect.currentframe", lambda: current_frame)

    # load default key-value pairs
    # ============================
    # monkeypatch implemented on prefixes and override other
    monkeypatch.setenv(
        "PYAUD_DATADIR", str(Path.home() / ".local" / "share" / pyaud.__name__)
    )
    monkeypatch.setenv(
        "PYAUD_CACHEDIR", str(Path.home() / ".cache" / pyaud.__name__)
    )
    monkeypatch.setenv("PYAUD_TIMED", "0")
    monkeypatch.setenv("PYAUD_FIX", "0")

    # prepare test locations
    # ======================
    # create test directories
    # ~/.cache/pyaud/log/pyaud.log needs to exist before running
    # ``logging.config.dictConfig(config: t.Dict[str, t.Any])``
    Path.cwd().mkdir()

    # initialize repository
    # =====================
    git.init(file=os.devnull)

    # create ~/.gitconfig
    # ===================
    config = ConfigParser(default_section="")
    config.read_dict(
        {
            "advice": {"detachedHead": "false"},
            "init": {"defaultBranch": "master"},
        }
    )
    with open(Path.home() / ".gitconfig", "w", encoding="utf-8") as fout:
        config.write(fout)

    mock_repo(rev_parse=lambda _: None, status=lambda _: None)
    monkeypatch.setattr(
        "pyaud.plugins._HashMapping.match_file", lambda *_: False
    )
    # noinspection PyProtectedMember
    monkeypatch.setattr("pyaud.plugins._plugins", pyaud.plugins._plugins)
    monkeypatch.setattr("pyaud.plugins.load", lambda: None)
    monkeypatch.setattr("pyaud._core._register_builtin_plugins", lambda: None)
    monkeypatch.setattr("pyaud.files.populate", lambda _: None)

    # setup singletons
    # ================
    pyaud.files.clear()
    pc.toml.clear()


@pytest.fixture(name="nocolorcapsys")
def fixture_nocolorcapsys(capsys: pytest.CaptureFixture) -> NoColorCapsys:
    """Instantiate capsys with the regex method.

    :param capsys: Capture ``sys`` stdout and stderr..
    :return: Instantiated ``NoColorCapsys`` object for capturing output
        stream and sanitizing the string if it contains ANSI escape
        codes.
    """
    return NoColorCapsys(capsys)


@pytest.fixture(name="main")
def fixture_main(monkeypatch: pytest.MonkeyPatch) -> MockMainType:
    """Pass patched commandline arguments to package's main function.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _main(*args: str) -> int:
        """Run main with custom args."""
        monkeypatch.setattr("sys.argv", [pyaud.__name__, *args])
        return main()

    return _main


@pytest.fixture(name="call_status")
def fixture_call_status() -> MockCallStatusType:
    """Disable all usage of function apart from selected returncode.

    Useful for processes programmed to return a value for the function
    depending on the value of ``__name__``.

    :return: Function for using this fixture.
    """

    def _call_status(module: str, returncode: int = 0) -> MockFuncType:
        def _func(*_: str, **__: bool) -> int:
            return returncode

        _func.__name__ = module
        return _func

    return _call_status


@pytest.fixture(name="patch_sp_call")
def fixture_patch_sp_call(monkeypatch: pytest.MonkeyPatch) -> MockSPCallType:
    """Mock ``Subprocess.call``.

    Print the command that is being run.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _patch_sp_call(func: MockFuncType, returncode: int = 0) -> None:
        def call(*args: str, **kwargs: bool) -> int:
            func(*args, **kwargs)

            return returncode

        monkeypatch.setattr("spall.Subprocess.call", call)

    return _patch_sp_call


@pytest.fixture(name="make_tree")
def fixture_make_tree() -> MakeTreeType:
    """Recursively create directory tree from dict mapping.

    :return: Function for using this fixture.
    """

    def _make_tree(root: str | Path, obj: t.Dict[str | Path, t.Any]) -> None:
        for key, value in obj.items():
            fullpath = Path(root) / key
            if isinstance(value, dict):
                fullpath.mkdir(exist_ok=True)
                _make_tree(fullpath, value)
            else:
                fullpath.touch()

    return _make_tree


@pytest.fixture(name="patch_sp_print_called")
def fixture_patch_sp_print_called(
    patch_sp_call: MockSPCallType,
) -> MockSPPrintCalledType:
    """Mock ``Subprocess.call``to print the command that is being run.

    :param patch_sp_call: Mock ``Subprocess.call`` by injecting a new
        function into it.
    :return: Function for using this fixture.
    """

    def _patch_sp_print_called() -> None:
        def _call(self, *args: str, **_: bool) -> int:
            print(f"{self} {' '.join(str(i) for i in args)}")
            return 0

        patch_sp_call(_call)

    return _patch_sp_print_called


@pytest.fixture(name="patch_sp_call_null")
def fixture_patch_sp_call_null(
    patch_sp_call: MockSPCallType,
) -> MockSPCallNullType:
    """Mock ``Subprocess.call``to do nothing and return returncode.

    :param patch_sp_call: Mock ``Subprocess.call`` by injecting a new
        function into it.
    :return: Function for using this fixture.
    """

    def _patch_sp_print_called() -> None:
        def _call(_, *__: str, **___: bool) -> int:
            return 0

        patch_sp_call(_call)

    return _patch_sp_print_called


@pytest.fixture(name="unpatch_setuptools_find_packages")
def fixture_unpatch_setuptools_find_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unpatch ``setuptools_find_packages``.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "setuptools.find_packages", original_setuptools_find_packages
    )


@pytest.fixture(name="mock_repo")
def fixture_mock_repo(monkeypatch: pytest.MonkeyPatch) -> FixtureMockRepo:
    """Mock ``git.Repo`` class.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _mock_repo(
        **kwargs: t.Callable[[VarArg(t.Any), KwArg(t.Any)], None]
    ) -> None:
        default_kwargs = {
            "rev_parse": lambda *_, **__: None,
            "status": lambda *_, **__: None,
            "rev_list": lambda *_, **__: "",
        }
        default_kwargs.update(kwargs)
        git_repo = type("Repo", (), {})
        git_repo.git = type("git", (), {})  # type: ignore
        for key, value in default_kwargs.items():
            setattr(git_repo.git, key, value)  # type: ignore

        monkeypatch.setattr("git.Repo", lambda _: git_repo)

    return _mock_repo


@pytest.fixture(name="mock_temporary_directory")
def fixture_mock_temporary_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> FixtureMockTemporaryDirectory:
    """Patch ``TemporaryDirectory`` to return test /tmp/<unique> dir.

    :param monkeypatch: Mock patch environment and attributes.
    :return: Function for using this fixture.
    """

    def _mock_temporary_dir(*temp_dirs: Path) -> None:
        monkeypatch.setattr(
            "pyaud_plugins._plugins.write.TemporaryDirectory",
            MockTemporaryDirectory(*temp_dirs).open,
        )

    return _mock_temporary_dir
