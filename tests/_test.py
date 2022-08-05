"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,protected-access
import os
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
    DEPLOY,
    DEPLOY_COV,
    DEPLOY_DOCS,
    DOCTEST,
    DOCTEST_PACKAGE,
    DOCTEST_README,
    FILE,
    FILES,
    FLAG_FIX,
    FLAG_SUPPRESS,
    FORMAT,
    INIT_REMOTE,
    INITIAL_COMMIT,
    NO_ISSUES,
    NO_TESTS_FOUND,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    README,
    REQUIREMENTS,
    SP_CALL,
    SP_OPEN_PROC,
    SP_REPR_PYTEST,
    SP_STDOUT,
    TEST,
    TESTS,
    TOC,
    TOKEN,
    TYPECHECK,
    WHITELIST,
    MakeTreeType,
    MockCallStatusType,
    MockMainType,
    MockSPCallNullType,
    MockSPOutputType,
    MockSPPrintCalledType,
    NoColorCapsys,
    git,
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
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
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
    pyaud.files.append(Path.cwd() / relpath)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    patch_sp_print_called()
    main(TESTS)
    assert nocolorcapsys.stdout().strip() == expected


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
    :param patch_sp_call_null: Mock ``Subprocess.call``to do nothing and
        return returncode.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / ppe.PACKAGE_TOC
    monkeypatch.setattr("pyaud_plugins._plugins.write.Toc.cache_file", path)
    make_tree(Path.cwd(), {ppe.DOCS.name: {ppe.DOCS_CONF.name: None}})
    template = templatest.templates.registered.getbyname("test-toc")
    patch_sp_call_null()
    with pytest.raises(pyaud.exceptions.AuditError):
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
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(TOC, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()
    assert ppe.PACKAGE_TOC.read_text(ppe.ENCODING) == template.expected
    path.write_text(CHANGE, ppe.ENCODING)
    main(TOC, FLAG_FIX)
    assert NO_ISSUES in nocolorcapsys.stdout()


def test_requirements(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    patch_sp_output: MockSPOutputType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test that requirements.txt file is correctly edited.

     Tested for use with ``pipfile2req``.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param patch_sp_output: Patch ``Subprocess`` so that ``call`` sends
        expected stdout out to self.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / ppe.REQUIREMENTS
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.Requirements.cache_file", path
    )
    main(REQUIREMENTS, FLAG_FIX)
    template = templatest.templates.registered.getbyname("test-requirements")
    ppe.PIPFILE_LOCK.write_text(template.template, ppe.ENCODING)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(REQUIREMENTS)

    patch_sp_output(templates.PIPFILE2REQ_PROD, templates.PIPFILE2REQ_DEV)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(REQUIREMENTS, FLAG_FIX)
    out = nocolorcapsys.stdout()
    assert NO_ISSUES in out
    assert ppe.REQUIREMENTS.read_text(ppe.ENCODING) == template.expected
    path.write_text(CHANGE, ppe.ENCODING)
    patch_sp_output(templates.PIPFILE2REQ_PROD, templates.PIPFILE2REQ_DEV)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(REQUIREMENTS, FLAG_FIX)
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
    monkeypatch.setattr("pyaud._cache._get_commit_hash", lambda: "hash")
    with pytest.raises(pyaud.exceptions.AuditError):
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
    main("lint", FLAG_SUPPRESS)
    assert "\x1b[0m" in capsys.readouterr()[0]


@pytest.mark.usefixtures(INIT_REMOTE)
def test_deploy_not_master(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test that deployment is skipped when branch is not ``master``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.deprecate.branch", lambda: "not_master"
    )
    main(DEPLOY_DOCS)
    assert "Documentation not for master" in nocolorcapsys.stdout()


@pytest.mark.usefixtures(INIT_REMOTE)
def test_deploy_master_not_set(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test correct notification is displayed.

    Test for when essential environment variables are not set in
    ``master``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setenv("PYAUD_GH_NAME", "")
    monkeypatch.setenv("PYAUD_GH_EMAIL", "")
    monkeypatch.setenv("PYAUD_GH_TOKEN", "")
    monkeypatch.delenv("PYAUD_GH_NAME")
    monkeypatch.delenv("PYAUD_GH_EMAIL")
    monkeypatch.delenv("PYAUD_GH_TOKEN")
    main(DEPLOY_DOCS)
    out = nocolorcapsys.stdout()
    assert "The following is not set:" in out
    assert "- PYAUD_GH_NAME" in out
    assert "- PYAUD_GH_EMAIL" in out
    assert "- PYAUD_GH_TOKEN" in out


@pytest.mark.usefixtures(INIT_REMOTE)
def test_deploy_master(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test docs are properly deployed.

    Test for when environment variables are set and checked out at
    ``master``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """

    def _docs(*_: str, **__: int) -> int:
        Path(Path.cwd() / ppe.BUILDDIR / "html").mkdir(parents=True)
        return 0

    mock_plugins = pyaud.plugins.mapping()
    mock_plugins[ppe.DOCS.name] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    ppe.README_RST.touch()  # force stash
    git.add(".")
    git.commit("-m", INITIAL_COMMIT, file=os.devnull)
    ppe.README_RST.write_text("package\n====\n", ppe.ENCODING)
    main(DEPLOY_DOCS, FLAG_FIX)
    out = nocolorcapsys.stdout()
    assert "Documentation Successfully deployed" in out
    main(DEPLOY_DOCS, FLAG_FIX)
    out = nocolorcapsys.stdout()
    assert "No difference between local branch and remote" in out


@pytest.mark.parametrize(
    "rounds,expected",
    [
        (1, "Pushing updated documentation"),
        (2, "No difference between local branch and remote"),
    ],
    ids=["stashed", "multi"],
)
@pytest.mark.usefixtures(INIT_REMOTE)
def test_deploy_master_param(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    rounds: int,
    expected: str,
) -> None:
    """Check that nothing happens when not checkout at master.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param rounds: How many times ``make_deploy_docs`` needs to be run.
    :param expected: Expected stdout result.
    """

    def _docs(*_: str, **__: bool) -> int:
        Path(ppe.BUILDDIR / "html").mkdir(parents=True)
        return 0

    mock_plugins = pyaud.plugins.mapping()
    mock_plugins[ppe.DOCS.name] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    ppe.README_RST.touch()
    Path(Path.cwd(), FILE).touch()
    git.add(".", file=os.devnull)
    git.commit("-m", INITIAL_COMMIT, file=os.devnull)
    for _ in range(rounds):
        main(DEPLOY_DOCS, FLAG_FIX)

    assert expected in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "file,env,expected",
    [
        (ppe.COVERAGE_XML.name, "CODECOV_TOKEN", "<Subprocess (codecov)>"),
        (ppe.COVERAGE_XML.name, "NOT_CODECOV_TOKEN", "CODECOV_TOKEN not set"),
        (ppe.WHITELIST.name, "CODECOV_TOKEN", "No coverage report found"),
        (ppe.WHITELIST.name, "NOT_CODECOV_TOKEN", "No coverage report found"),
    ],
    ids=["file-set", "file-not-set", "no-file-set", "no-file-not-set"],
)
def test_deploy_cov_token(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
    file: Path,
    env: str,
    expected: str,
) -> None:
    """Test ``pyaud deploy-cov`` token.

    Test when ``CODECOV_TOKEN`` is set and not set and a coverage.xml
    file exists.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param file: File to create.
    :param env: Environment variable to set.
    :param expected: Expected result from stdout.
    """
    Path(Path.cwd() / file).touch()
    patch_sp_print_called()
    monkeypatch.setenv(env, TOKEN)
    main(DEPLOY_COV)
    assert expected in nocolorcapsys.stdout()


def test_download_missing_stubs(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test for coverage on missing stubs file.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    """
    pyaud.files.append(Path.cwd() / FILE)
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
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(SP_STDOUT, lambda _: [])
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(TYPECHECK)

    assert str(err.value) == "pyaud typecheck did not pass all checks"


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
    with pytest.raises(pyaud.exceptions.AuditError):
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
    stderr = "pyaud doctest-readme did not pass all checks"
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 0)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(DOCTEST_README)
    assert stdout in nocolorcapsys.stdout()
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(DOCTEST_README)

    assert str(err.value) == stderr


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
    pyaud.files.append(path)
    test_obj = {"tool": {"b_package": {"key1": "value1"}}}
    with open(ppe.PYPROJECT, "wb") as fout:
        tomli_w.dump(test_obj, fout)

    main("sort-pyproject")
    assert NO_ISSUES in nocolorcapsys.stdout()
    test_obj = {
        "tool": {
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
        (README, "<Subprocess (readmetester)>"),
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
    pyaud.files.append(Path.cwd() / FILE)
    patch_sp_print_called()
    main(module)
    assert expected in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "module,plugins",
    [
        (DEPLOY, [DEPLOY_COV, DEPLOY_DOCS]),
        (FILES, [REQUIREMENTS, TOC, WHITELIST]),
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


def test_get_branch_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ``branch`` returns None.

    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.deprecate.git.stdout", lambda: []
    )
    assert pplugins._plugins.deprecate.branch() is None
