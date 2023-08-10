"""
tests._test
===========
"""
import subprocess

# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,protected-access,no-member
import typing as t
from pathlib import Path

import pyaud
import pytest
import templatest
import tomli_w

import pyaud_plugins as pplugins
from pyaud_plugins import environ as ppe

from . import (
    CHANGE,
    CONST,
    COVERAGE,
    DOCTEST,
    DOCTEST_PACKAGE,
    DOCTEST_README,
    FILE,
    FILES,
    FLAG_FIX,
    FORMAT,
    GIT,
    INIT,
    NO_ISSUES,
    NO_TESTS_FOUND,
    PACKAGE,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    README,
    README_HELP,
    README_HELP_CACHE_FILE,
    REPO,
    SP_CALL,
    SP_OPEN_PROC,
    SP_REPR_PYTEST,
    SP_STDOUT,
    TEST,
    TESTS,
    TOC,
    TOOL,
    TYPECHECK,
    WHITELIST,
    FixtureMockTemporaryDirectory,
    MakeTreeType,
    MockCallStatusType,
    MockMainType,
    MockSPCallNullType,
    MockSPPrintCalledType,
    NoColorCapsys,
    templates,
)


@pytest.mark.parametrize(
    "is_tests,expected", [(False, "No coverage to report"), (True, "xml")]
)
def test_call_coverage_xml(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
    is_tests: bool,
    expected: str,
) -> None:
    """Test ``coverage xml`` is called after successful test run.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called`.
    :param is_tests: Are there any tests available? True or False.
    :param expected: Expected output.
    """

    class _Tests(pplugins._plugins.action.Tests):
        @property
        def is_tests(self) -> bool:
            return is_tests

        def action(self, *args: str, **kwargs: bool) -> int:
            return 0

    patch_sp_print_called()
    pplugins._plugins.action.Coverage.__bases__ = (_Tests,)
    del pyaud.plugins._plugins[COVERAGE]
    pyaud.plugins._plugins[COVERAGE] = pplugins._plugins.action.Coverage
    main(COVERAGE)
    assert expected in nocolorcapsys.stdout()


def test_docs(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    call_status: MockCallStatusType,
    make_tree: MakeTreeType,
) -> None:
    """Test ``pyaud docs``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param call_status: Patch function to return specific exit-code.
    :param make_tree: Create directory tree from dict mapping.
    """

    def _call(*_: str, **__: bool) -> int:
        ppe.BUILDDIR.mkdir(parents=True)
        return 0

    mocked_plugins = pyaud.plugins.mapping()
    mocked_plugins[TOC] = call_status(TOC)  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    monkeypatch.setattr(SP_CALL, _call)
    make_tree(
        Path.cwd(),
        {
            ppe.README_RST.name: None,
            ppe.DOCS.name: {ppe.DOCS_CONF.name: None, "readme.rst": None},
        },
    )
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda _: None)
    main(ppe.DOCS.name)


@pytest.mark.parametrize(
    "relpath,expected",
    [
        (Path(ppe.TESTS.name), NO_TESTS_FOUND),
        (Path(ppe.TESTS.name, "test.py"), NO_TESTS_FOUND),
        (Path(ppe.TESTS.name, "filename.py"), NO_TESTS_FOUND),
        (Path(ppe.TESTS.name, "_test.py"), SP_REPR_PYTEST),
        (Path(ppe.TESTS.name, "test_.py"), SP_REPR_PYTEST),
        (Path(ppe.TESTS.name, "three_test.py"), SP_REPR_PYTEST),
        (Path(ppe.TESTS.name, "test_four.py"), SP_REPR_PYTEST),
    ],
    ids=(
        ppe.TESTS.name,
        "tests/test.py",
        "tests/filename.py",
        "tests/test_.py",
        "tests/_test.py",
        "tests/three_test.py",
        "tests/test_four.py",
    ),
)
def test_pytest_is_tests(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
    relpath: Path,
    expected: str,
) -> None:
    """Test that ``pytest`` is correctly called.

    Test that ``pytest`` is not called if:

        - there is a test dir without tests
        - incorrect names within tests dir
        - no tests at all within tests dir.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called`.
    :param relpath: Relative path to file.
    :param expected: Expected stdout.
    """
    path = Path.cwd() / relpath
    path.parent.mkdir(exist_ok=True)
    path.touch()
    pyaud.files.append(path)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda _: None)
    patch_sp_print_called()
    main(TESTS)
    assert expected in nocolorcapsys.stdout().strip()


def test_toc(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    make_tree: MakeTreeType,
    patch_sp_call_null: MockSPCallNullType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test that the default toc file is edited correctly.

    Ensure additional files generated by ``sphinx-api`` doc are removed.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param patch_sp_call_null: Mock ``Subprocess.call`` to do nothing
        and return returncode.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / ppe.PACKAGE_TOC
    monkeypatch.setattr("pyaud_plugins._plugins.write.Toc.cache_file", path)
    make_tree(Path.cwd(), {ppe.DOCS.name: {ppe.DOCS_CONF.name: None}})
    template = templatest.templates.registered.getbyname("test-toc")
    patch_sp_call_null()
    main(TOC)

    class _TempDir:
        def __enter__(self) -> Path:
            return tmp_path

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Nothing to do."""

    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.tempfile.TemporaryDirectory", _TempDir
    )
    package_toc = tmp_path / ppe.PACKAGE_TOC.name
    package_toc.write_text(template.template, ppe.ENCODING)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda _: None)
    main(TOC, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert ppe.PACKAGE_TOC.read_text(ppe.ENCODING) == template.expected
    path.write_text(CHANGE, ppe.ENCODING)
    main(TOC, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


def test_whitelist(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test a whitelist.py file is created properly.

    Test for when piping data from ``vulture --make-whitelist``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / "whitelist.py"
    template = templatest.templates.registered.getbyname("test-whitelist")
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.Whitelist.cache_file", path
    )
    monkeypatch.setattr(
        "spall.Subprocess.stdout",
        lambda *_, **__: template.template.splitlines(),
    )
    main(WHITELIST)

    main(WHITELIST, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert ppe.WHITELIST.read_text(ppe.ENCODING) == template.expected
    path.write_text(CHANGE, ppe.ENCODING)
    main(WHITELIST, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


def test_pycharm_hosted(
    main: MockMainType, capsys: pytest.CaptureFixture
) -> None:
    """Test that color codes are produced with ``PYCHARM_HOSTED``.

    :param main: Patch package entry point.
    :param capsys: Capture sys output.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text("import this_package_does_not_exist", ppe.ENCODING)
    main("lint")
    assert "\x1b[0m" in capsys.readouterr()[0]


def test_download_missing_stubs(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test for coverage on missing stubs file.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    path.touch()
    pyaud.files.append(path)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    stdout = ["error: Library stubs not installed for"]
    monkeypatch.setattr(SP_STDOUT, lambda _: stdout)
    main(TYPECHECK)


def test_typecheck_re_raise_err(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test for re-raise of error for non stub library errors.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    path.touch()
    pyaud.files.append(path)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(SP_STDOUT, lambda _: [])
    main(TYPECHECK)


def test_nested_toc(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    make_tree: MakeTreeType,
) -> None:
    """Test that only one file is completed with a nested project.

    Prior to this commit only ``repo.src.rst`` would be removed.

    This commit will remove any file and copy its contents to the
    single <NAME>.rst file e.g. ``repo.routes.rst`` is removed and
    ``repo.routes``, ``repo.routes.auth``, ``repo.routes.post``, and
    ``repo.routes.views`` is added to repo.rst.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.Toc.cache_file",
        Path.cwd() / ppe.PACKAGE_TOC,
    )
    make_tree(
        Path.cwd(),
        {
            ppe.DOCS.name: {ppe.DOCS_CONF.name: None},
            ppe.PACKAGE_NAME: {
                "routes": {
                    "auth.py": None,
                    "__init__.py": None,
                    "post.py": None,
                    "views.py": None,
                },
                "admin.py": None,
                "cli.py": None,
                "config.py": None,
                "deps.py": None,
                "exceptions.py": None,
                "extensions.py": None,
                "forms.py": None,
                "__init__.py": None,
                "log.py": None,
                "mail.py": None,
                "models.py": None,
                "navbar.py": None,
                "redirect.py": None,
                "renderers.py": None,
                "security.py": None,
                "shell.py": None,
                "tasks.py": None,
                "user.py": None,
            },
        },
    )
    main(TOC)
    main(TOC, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert (
        ppe.PACKAGE_TOC.read_text(ppe.ENCODING)
        == templates.EXPECTED_NESTED_TOC
    )


def test_call_doctest_readme(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test success and failure with ``doctest-readme`` plugin.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    stdout = "Success: No issues found in README.rst"
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 0)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda _: None)
    assert main(DOCTEST_README) == 0
    assert stdout in nocolorcapsys.stdout()
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda _: None)
    assert main(DOCTEST_README) == 1


def test_call_sort_pyproject(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test register and call of ``sort-pyproject`` plugin.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.SortPyproject.cache_file",
        Path.cwd() / ppe.PYPROJECT,
    )
    path = Path.cwd() / FILE
    path.touch()
    pyaud.files.append(path)
    test_obj = {TOOL: {"b_package": {"key1": "value1"}}}
    with open(ppe.PYPROJECT, "wb") as fout:
        tomli_w.dump(test_obj, fout)

    main("sort-pyproject")
    assert NO_ISSUES in nocolorcapsys.stdout()
    test_obj = {
        TOOL: {
            "b_package": {"key2": "value2"},
            "a_package": {"key3": "value3"},
        }
    }
    with open(ppe.PYPROJECT, "wb") as fout:
        tomli_w.dump(test_obj, fout)

    main("sort-pyproject", FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "module,expected",
    [
        (DOCTEST_PACKAGE, "<Subprocess (sphinx-build)> -M doctest"),
        (CONST, "<Subprocess (constcheck)>"),
        (TYPECHECK, "<Subprocess (mypy)> --ignore-missing-imports"),
        (FORMAT, "<Subprocess (black)>"),
        ("params", "<Subprocess (docsig)>"),
    ],
)
def test_action(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
    module: str,
    expected: str,
) -> None:
    """Test calling of ``Action`` plugin.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param module: Name of module to call.
    :param expected: Expected result.
    """
    path = Path.cwd() / FILE
    path.touch()
    pyaud.files.append(path)
    patch_sp_print_called()
    main(module)
    assert expected in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "module,plugins",
    [
        (FILES, [TOC, WHITELIST]),
        (DOCTEST, [DOCTEST_PACKAGE, DOCTEST_README]),
        (TEST, [DOCTEST, COVERAGE]),
    ],
)
def test_parametrize(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    call_status: MockCallStatusType,
    module: str,
    plugins: t.Tuple[str, str],
) -> None:
    """Test the correct plugins are called when using ``Parametrize``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param call_status: Patch function to not do anything. Optionally
        returns non-zero exit code (0 by default).
    :param module: Name of module to call.
    :param plugins: Plugins belonging to class.
    """
    mocked_plugins = pyaud.plugins.mapping()
    for plugin in plugins:
        mocked_plugins[plugin] = call_status(plugin)  # type: ignore

    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    main(module)
    out = nocolorcapsys.stdout().splitlines()
    assert all(f"{pyaud.__name__} {i}" in out for i in plugins)


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""
    path = Path.cwd() / README

    # def _test_file_index(title: str, underline: str) -> None:

    repo = "repo"
    readme = "README"
    repo_underline = len(repo) * "="
    readme_underline = len(readme) * "="
    path.write_text(f"{repo}\n{repo_underline}\n", ppe.ENCODING)
    assert f"{repo}\n{repo_underline}" in path.read_text(ppe.ENCODING)
    # noinspection PyUnresolvedReferences
    with pplugins._parsers.LineSwitch(path, {0: readme, 1: readme_underline}):
        assert f"{readme}\n{readme_underline}" in path.read_text(ppe.ENCODING)

    assert f"{repo}\n{repo_underline}" in path.read_text(ppe.ENCODING)


def test_about_tests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    make_tree: MakeTreeType,
    nocolorcapsys: NoColorCapsys,
    mock_temporary_directory: FixtureMockTemporaryDirectory,
) -> None:
    """Test test README is formatted correctly.

    :param tmp_path: Create and return temporary directory.
    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param mock_temporary_directory: Mock
        ``tempfile.TemporaryDirectory``.
    """
    tempdir = tmp_path / "tmp"
    about_tests = "about-tests"
    path = tempdir / ppe.ABOUT_TESTS

    # this will get run three times, when the audit fails and then when
    # it passes (not sure why there's a third...)
    mock_temporary_directory(tempdir, tempdir, tempdir)
    markdown_file = tempdir / "docs" / "_build" / "markdown" / "tests.md"
    (Path.cwd() / "README.rst").touch()
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.AboutTests.cache_file", path
    )
    template = templatest.templates.registered.getbyname("test-about-tests")
    make_tree(
        Path.cwd(),
        {ppe.DOCS.name: {ppe.DOCS_CONF.name: None}, ppe.TESTS.name: {}},
    )

    def _call(*_: t.Any, **__: t.Any) -> None:
        markdown_file.parent.mkdir(exist_ok=True, parents=True)
        markdown_file.write_text(template.template)

    monkeypatch.setattr(SP_CALL, _call)
    main(about_tests)
    main(about_tests, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert path.read_text(ppe.ENCODING) == template.expected
    main(about_tests, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


def test_commit_policy(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    make_tree: MakeTreeType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test commit policy generation from .conform.yaml.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    commit_policy = "commit-policy"
    path = Path.cwd() / ppe.COMMIT_POLICY
    conform_yaml = Path.cwd() / ".conform.yaml"
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.CommitPolicy.cache_file", path
    )
    template = templatest.templates.registered.getbyname("test-commit-policy")
    make_tree(Path.cwd(), {".github": {}})

    main(commit_policy, FLAG_FIX)
    conform_yaml.write_text(template.template)
    main(commit_policy)
    main(commit_policy, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert path.read_text(ppe.ENCODING) == template.expected
    main(commit_policy, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


# noinspection PyUnresolvedReferences
@pytest.mark.usefixtures("unpatch_setuptools_find_packages")
def test_get_packages(make_tree: MakeTreeType) -> None:
    """Test process when searching for project's package.

    :param make_tree: Create directory tree from dict mapping.
    """
    # search for only package
    # =======================
    make_tree(Path.cwd(), {PACKAGE[1]: {INIT: None}})
    assert pplugins._utils.get_packages() == [PACKAGE[1]]
    assert pplugins._utils.package() == PACKAGE[1]

    # search for ambiguous package
    # ============================
    make_tree(Path.cwd(), {PACKAGE[2]: {INIT: None}, PACKAGE[3]: {INIT: None}})
    assert pplugins._utils.get_packages() == [
        PACKAGE[1],
        PACKAGE[2],
        PACKAGE[3],
    ]
    assert pplugins._utils.package() is None

    # search for package with the same name as repo
    # =============================================
    make_tree(Path.cwd(), {REPO: {INIT: None}})
    assert pplugins._utils.get_packages() == [
        REPO,
        PACKAGE[1],
        PACKAGE[2],
        PACKAGE[3],
    ]
    assert pplugins._utils.package() == REPO
    (Path.cwd() / "pyproject.toml").write_text(
        tomli_w.dumps({TOOL: {"poetry": {"name": PACKAGE[2]}}})
    )
    assert pplugins._utils.package() == PACKAGE[2].replace("-", "_")


@pytest.mark.parametrize(
    "commit_message,diff",
    [
        ("refactor: commit message\nsigned off by", ""),
        (
            "add: commit message\nsigned off by",
            "### Added\n+- Add additional info for audit",
        ),
    ],
    ids=["no-change-tag", "change-tag-logged"],
)
def test_change_logged_pass(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    commit_message: str,
    diff: str,
) -> None:
    """Test change-logged when passing.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param commit_message: Commit message to mock.
    :param diff: CHANGELOG diff to mock.
    """

    class _Repo:
        def __init__(self, _) -> None:
            self.head = type("head", (), {})  # type: ignore
            self.head.commit = type("commit", (), {})  # type: ignore
            self.head.commit.message = commit_message  # type: ignore
            self.git = type(GIT, (), {})  # type: ignore
            self.git.diff = self.diff  # type: ignore

        @staticmethod
        def diff(*_, **__) -> str:
            """Return patched diff."""
            return diff

    change_logged = "change-logged"
    _git = type(GIT, (), {})  # type: ignore
    _git.Repo = _Repo  # type: ignore
    monkeypatch.setattr("pyaud_plugins._plugins.action.git", _git)
    assert main(change_logged) == 0


@pytest.mark.parametrize(
    "commit_message,diff",
    [
        ("add: commit message\nsigned off by", ""),
        (
            "add: commit message\nsigned off by",
            "### Changed\n+- Add additional info for audit",
        ),
    ],
    ids=["change-tag-not-logged", "change-tag-logged-wrong"],
)
def test_change_logged_fail(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    commit_message: str,
    diff: str,
) -> None:
    """Test change-logged when failing.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param commit_message: Commit message to mock.
    :param diff: CHANGELOG diff to mock.
    """

    class _Repo:
        def __init__(self, _) -> None:
            self.head = type("head", (), {})  # type: ignore
            self.head.commit = type("commit", (), {})  # type: ignore
            self.head.commit.message = commit_message  # type: ignore
            self.git = type(GIT, (), {})  # type: ignore
            self.git.diff = self.diff  # type: ignore

        @staticmethod
        def diff(*_, **__) -> str:
            """Return patched diff."""
            return diff

    change_logged = "change-logged"
    _git = type(GIT, (), {})  # type: ignore
    _git.Repo = _Repo  # type: ignore
    monkeypatch.setattr("pyaud_plugins._plugins.action.git", _git)
    main(change_logged)


def test_readme_help(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    make_tree: MakeTreeType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test commit policy generation from .conform.yaml.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    make_tree(Path.cwd(), {ppe.README_RST: None})
    path = Path.cwd() / ppe.README_RST
    executable = Path.cwd() / "docsig"
    monkeypatch.setattr(README_HELP_CACHE_FILE, path)
    template = templatest.templates.registered.getbyname("test-readme-help")

    path.write_text(template.template)
    executable.write_text(templates.EXECUTABLE)
    run = subprocess.run
    monkeypatch.setattr(
        "subprocess.run",
        lambda *_, **__: run(
            ["python3", executable, "--help"], capture_output=True, check=True
        ),
    )
    main(README_HELP)
    main(README_HELP, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert path.read_text(ppe.ENCODING) == template.expected
    main(README_HELP, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


def test_readme_help_no_commandline(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    make_tree: MakeTreeType,
) -> None:
    """Test commit policy generation from .conform.yaml.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {ppe.README_RST: None})
    path = Path.cwd() / ppe.README_RST
    monkeypatch.setattr(README_HELP_CACHE_FILE, path)
    path.write_text(templates.README_NO_COMMANDLINE_HELP)
    assert main(README_HELP) == 0


def test_readme_help_no_readme_rst(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test commit policy generation from .conform.yaml.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    path = Path.cwd() / ppe.README_RST
    monkeypatch.setattr(README_HELP_CACHE_FILE, path)
    assert main(README_HELP) == 0
