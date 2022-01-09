"""
tests_test
==========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,unused-variable,protected-access
import datetime
import os
import typing as t
from pathlib import Path

# noinspection PyPackageRequirements
import pyaud
import pytest

import pyaud_plugins

from . import (
    CONFPY,
    DOCS,
    FILES,
    INIT,
    INITIAL_COMMIT,
    NO_ISSUES,
    PIPFILE_LOCK,
    PUSHING_SKIPPED,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    README,
    REPO,
    SP_CALL,
    SP_OPEN_PROC,
    SP_STDOUT,
    NoColorCapsys,
    files,
)
from .files import EXPECTED_NESTED_TOC


def test_no_files_found(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test the correct output is produced when no file exists.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main("typecheck")
    assert nocolorcapsys.stdout().strip() == "No files found"


@pytest.mark.parametrize(
    "contents,expected",
    [
        (["created"], "created ``whitelist.py``"),
        (["", "updated"], "updated ``whitelist.py``"),
        (
            ["up-to-date", "up-to-date"],
            "``whitelist.py`` is already up to date",
        ),
    ],
    ids=("created", "updated", "up_to_date"),
)
def test_write_command(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    contents: t.List[str],
    expected: str,
) -> None:
    """Test the ``@write_command`` decorator.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param monkeypatch: Mock patch environment and attributes.
    :param contents: Content to write to file.
    :param expected: Expected output.
    """
    for content in contents:

        def mock_write_whitelist(*_: t.Any, **__: t.Any) -> None:
            with open(
                Path.cwd() / pyaud.environ.WHITELIST, "w", encoding="utf-8"
            ) as fout:
                fout.write(content)

        monkeypatch.setattr(
            "pyaud_plugins.modules.Whitelist.write", mock_write_whitelist
        )
        main("whitelist")

    assert expected in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "is_tests,expected", [(False, "No coverage to report"), (True, "xml")]
)
def test_call_coverage_xml(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    is_tests: bool,
    expected: str,
) -> None:
    """Test ``coverage xml`` is called after successful test run.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param is_tests: Are there any tests available? True or False.
    :param expected: Expected output.
    """

    class _HasCall:
        @classmethod
        def call(cls, *args: t.Any, **_: t.Any) -> None:
            """Print the args passed to the subprocess object.

            :param args: Args to print.
            :param _: Unused misc kwargs.
            """
            print(*args)

    class _Tests(  # pylint: disable=too-few-public-methods
        pyaud_plugins.modules.Tests
    ):
        @property
        def is_tests(self) -> bool:
            return is_tests

        def action(self, *args: t.Any, **kwargs: bool) -> t.Any:
            return 0

    monkeypatch.setattr(
        "pyaud.plugins._SubprocessFactory", lambda *_: {"coverage": _HasCall}
    )
    coverage = pyaud_plugins.modules.Coverage
    coverage.__bases__ = (_Tests,)
    del pyaud.plugins._plugins["coverage"]
    pyaud.plugins._plugins["coverage"] = coverage
    main("coverage")
    assert nocolorcapsys.stdout().strip() == expected


def test_make_deploy_all(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    call_status: t.Any,
) -> None:
    """Test the correct commands are run when running ``pyaud deploy``.

    Patch functions with ``call_status`` to remove functionality from
    function and only return a zero exit-status. ``make_deploy_*``
    functions should still be able to print what functions are being run
    as announced to the console in cyan.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param call_status: Patch function to not do anything. Optionally
        returns non-zero exit code (0 by default).
    """
    modules = "deploy-cov", "deploy-docs"
    mocked_plugins = pyaud.plugins.mapping()
    for module in modules:
        mocked_plugins[module] = call_status(module)

    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    main("deploy")
    out = nocolorcapsys.stdout().splitlines()
    for module in modules:
        assert f"{pyaud.__name__} {module}" in out


def test_make_deploy_all_fail(
    main: t.Any,
    call_status: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test ``pyaud deploy`` fails correctly when encountering an error.

    :param main: Patch package entry point.
    :param call_status: Patch function to return specific exit-code.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    deploy_module = "deploy-docs"
    mock_plugins = pyaud.plugins.mapping()
    mock_plugins[deploy_module] = call_status(deploy_module, 1)
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    main("deploy")
    out = nocolorcapsys.stdout().splitlines()
    assert f"{pyaud.__name__} {deploy_module}" in out


def test_make_docs_no_docs(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test correct message is produced.

    Test when running ``pyaud docs`` when no docs are present.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    Path(Path.cwd() / FILES).touch()
    main("docs")
    assert nocolorcapsys.stdout().strip() == "No docs found"


def test_make_docs_toc_fail(
    main: t.Any, monkeypatch: pytest.MonkeyPatch, make_tree: t.Any
) -> None:
    """Test that error message is produced when ``make_toc`` fails.

    Test process stops when ``make_toc`` fails before running the main
    ``make_docs`` process.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {"docs": {CONFPY: None}})
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main("docs")

    assert str(err.value) == "pyaud docs did not pass all checks"


def test_make_docs_rm_cache(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    call_status: t.Any,
    make_tree: t.Any,
) -> None:
    """Test ``make_docs`` removes all builds before starting a new one.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param call_status: Patch function to return specific exit-code.
    :param make_tree: Create directory tree from dict mapping.
    """
    builddir = Path.cwd() / pyaud.environ.BUILDDIR
    readme = Path.cwd() / README

    # disable call to ``Subprocess`` to only create ./docs/_build
    # directory so tests can continue
    def _call(*_: t.Any, **__: t.Any) -> int:
        builddir.mkdir(parents=True)
        return 0

    # patch ``make_toc`` and ``Subprocess.call``
    mocked_plugins = pyaud.plugins.mapping()
    mocked_plugins["toc"] = call_status("toc")
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    monkeypatch.setattr(SP_CALL, _call)
    make_tree(Path.cwd(), {"docs": {CONFPY: None, "readme.rst": None}})
    with open(readme, "w", encoding="utf-8") as fout:
        fout.write(files.README_RST)

    builddir.mkdir(parents=True)
    Path(builddir / "marker").touch()
    freeze_docs_build = builddir.iterdir()

    # to test creation of README.rst content needs to be written to file
    with open(readme, "w", encoding="utf-8") as fout:
        fout.write(files.README_RST)

    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main("docs")
    assert freeze_docs_build != builddir.iterdir()


def test_make_files(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    call_status: t.Any,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test correct commands are executed when running ``make_files``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param call_status: Patch function to return specific exit-code.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    file_funcs = "requirements", "toc", "whitelist"
    mocked_modules = pyaud.plugins.mapping()
    for file_func in file_funcs:
        mocked_modules[file_func] = call_status(file_func)

    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_modules)

    main("files")
    assert (
        nocolorcapsys.stdout()
        == "\npyaud requirements\n\npyaud toc\n\npyaud whitelist\n"
    )


def test_make_format(main: t.Any) -> None:
    """Test ``make_format`` when successful and when it fails.

    :param main: Patch package entry point.
    """
    file = Path.cwd() / FILES
    with open(file, "w", encoding="utf-8") as fout:
        fout.write(files.UNFORMATTED)

    pyaud.files.append(file)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("format")


def test_pipfile2req_commands(
    main: t.Any, patch_sp_print_called: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test that the correct commands are executed.

    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    requirements = Path.cwd() / pyaud.environ.REQUIREMENTS
    pipfile_lock = Path.cwd() / PIPFILE_LOCK
    with open(pipfile_lock, "w", encoding="utf-8") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_print_called()
    main("requirements")
    out = nocolorcapsys.stdout()
    assert all(
        e in out
        for e in (
            f"Updating ``{requirements}``",
            f"<Subprocess (pipfile2req)> {pipfile_lock}",
            f"<Subprocess (pipfile2req)> {pipfile_lock} --dev",
            f"created ``{requirements.name}``",
        )
    )


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""
    path = Path.cwd() / README

    def _test_file_index(title: str, underline: str) -> None:
        with open(path, encoding="utf-8") as fin:
            lines = fin.read().splitlines()

        assert lines[0] == title
        assert lines[1] == len(underline) * "="

    repo = "repo"
    readme = "README"
    repo_underline = len(repo) * "="
    readme_underline = len(readme) * "="
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(f"{repo}\n{repo_underline}\n")

    _test_file_index(repo, repo_underline)
    with pyaud.parsers.LineSwitch(path, {0: readme, 1: readme_underline}):
        _test_file_index(readme, readme_underline)

    _test_file_index(repo, repo_underline)


def test_append_whitelist(
    main: t.Any, nocolorcapsys: NoColorCapsys, patch_sp_print_called: t.Any
) -> None:
    """Test that whitelist file argument is appended ``vulture`` call.

    Test for when whitelist.py exists and is not appended if it does
    not, thus avoiding an error.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    project_dir = Path.cwd()
    whitelist = project_dir / pyaud.environ.WHITELIST
    Path(project_dir / FILES).touch()
    whitelist.touch()
    pyaud.git.add(".")
    pyaud.files.populate()
    patch_sp_print_called()
    main("unused")
    assert str(whitelist) in nocolorcapsys.stdout()


def test_mypy_expected(
    main: t.Any, patch_sp_print_called: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test that the ``mypy`` command is correctly called.

    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path(os.getcwd(), FILES)
    pyaud.files.append(path)
    patch_sp_print_called()
    main("typecheck")
    assert (
        f"<Subprocess (mypy)> --ignore-missing-imports {path}"
        in nocolorcapsys.stdout()
    )


@pytest.mark.parametrize(
    "relpath,expected",
    [
        (Path("tests"), "No tests found"),
        (Path("tests", "test.py"), "No tests found"),
        (Path("tests", "filename.py"), "No tests found"),
        (Path("tests", "_test.py"), "<Subprocess (pytest)>"),
        (Path("tests", "test_.py"), "<Subprocess (pytest)>"),
        (Path("tests", "three_test.py"), "<Subprocess (pytest)>"),
        (Path("tests", "test_four.py"), "<Subprocess (pytest)>"),
    ],
    ids=(
        "tests",
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
    main: t.Any,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: t.Any,
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
        announce what is called`
    :param relpath: Relative path to file.
    :param expected: Expected stdout.
    """
    pyaud.files.append(Path.cwd() / relpath)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    patch_sp_print_called()
    main("tests")
    assert nocolorcapsys.stdout().strip() == expected


def test_make_toc(
    monkeypatch: pytest.MonkeyPatch,
    main: t.Any,
    patch_sp_print_called: t.Any,
    make_tree: t.Any,
) -> None:
    """Test that the default toc file is edited correctly.

    Ensure additional files generated by ``sphinx-api`` doc are removed.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param make_tree: Create directory tree from dict mapping.
    """
    project_dir = Path.cwd()
    modules = "modules.rst"
    path = project_dir / DOCS / f"{REPO}.rst"
    make_tree(project_dir, {"docs": {modules: None, CONFPY: None}})
    with open(path, "w", encoding="utf-8") as fout:
        assert fout.write(files.DEFAULT_TOC)

    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    patch_sp_print_called()
    main("toc")
    with open(path, encoding="utf-8") as fin:
        assert fin.read() == files.ALTERED_TOC

    assert not Path(project_dir / DOCS / modules).is_file()


def test_make_requirements(
    monkeypatch: pytest.MonkeyPatch,
    main: t.Any,
    patch_sp_output: t.Any,
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
    path = Path.cwd() / pyaud.environ.REQUIREMENTS
    with open(Path.cwd() / PIPFILE_LOCK, "w", encoding="utf-8") as fout:
        fout.write(files.PIPFILE_LOCK)

    patch_sp_output(files.PIPFILE2REQ_PROD, files.PIPFILE2REQ_DEV)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main("requirements")
    assert nocolorcapsys.stdout() == (
        f"Updating ``{path}``\ncreated ``{path.name}``\n"
    )
    with open(path, encoding="utf-8") as fin:
        assert fin.read() == files.REQUIREMENTS


def test_make_whitelist(
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: t.Any,
) -> None:
    """Test a whitelist.py file is created properly.

    Test for when piping data from ``vulture --make-whitelist``.

    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    project_dir = Path.cwd()
    whitelist = project_dir / pyaud.environ.WHITELIST
    make_tree(
        project_dir,
        {
            "tests": {"conftest.py": None, FILES: None},
            "pyaud": {"src": {INIT: None, "modules.py": None}},
        },
    )
    pyaud.git.init(devnull=True)
    pyaud.git.add(".")
    pyaud.files.populate()
    monkeypatch.setattr(
        "pyaud._subprocess.Subprocess.stdout",
        lambda *_, **__: files.Whitelist.be8a443,
    )
    pyaud.plugins.get("whitelist")()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{whitelist}``\ncreated ``{whitelist.name}``\n"
    )
    with open(whitelist, encoding="utf-8") as fin:
        assert fin.read() == files.Whitelist.be8a443_all()


def test_pylint_colorized(main: t.Any, capsys: t.Any) -> None:
    """Test that color codes are produced with ``process.PIPE``.

    Test ``pylint --output-format=colorized``. If ``colorama`` is
    installed and a process calls ``colorama.init()`` a process pipe
    will be stripped. Using environment variable ``PYCHARM_HOSTED`` for
    now as a workaround as this voids this action.

    :param main: Patch package entry point.
    :param capsys: Capture sys output.
    """
    path = Path.cwd() / FILES
    with open(path, "w", encoding="utf-8") as fout:
        fout.write("import this_package_does_not_exist")

    pyaud.files.append(path)
    main("lint", "--suppress")
    output = capsys.readouterr()[0]
    assert all(
        i in output
        for i in ["\x1b[7;33m", "\x1b[0m", "\x1b[1m", "\x1b[1;31m", "\x1b[35m"]
    )


def test_isort_imports(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test isort properly sorts file imports.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILES
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(files.IMPORTS_UNSORTED)

    pyaud.files.append(path)
    main("imports", "--fix")
    with open(path, encoding="utf-8") as fin:
        assert (
            files.IMPORTS_SORTED.splitlines()[1:]
            == fin.read().splitlines()[:20]
        )

    out = nocolorcapsys.stdout()
    assert all(i in out for i in (f"Fixed {path.name}", NO_ISSUES))
    main("imports")


def test_readme(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test standard README and return values.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main("readme")
    assert (
        nocolorcapsys.stdout().strip() == "No README.rst found in project root"
    )
    with open(Path.cwd() / README, "w", encoding="utf-8") as fout:
        fout.write(files.CODE_BLOCK_TEMPLATE)

    main("readme")
    assert (
        "\n".join([i.strip() for i in nocolorcapsys.stdout().splitlines()])
        == files.CODE_BLOCK_EXPECTED
    )


@pytest.mark.parametrize(
    "module,content",
    [
        ("format", files.UNFORMATTED),
        ("imports", files.IMPORTS_UNSORTED),
        ("format-str", files.FORMAT_STR_FUNCS_PRE),
        ("format-docs", files.DOCFORMATTER_EXAMPLE),
    ],
    ids=["format", "imports", "format-str", "format-docs"],
)
def test_py_audit_error(
    main: t.Any, make_tree: t.Any, module: str, content: str
) -> None:
    """Test ``AuditError`` message.

    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param module: [<module>].__name__.
    :param content: Content to write to file.
    """
    project_dir = Path.cwd()
    file = project_dir / FILES
    make_tree(project_dir, {"tests": {"_test.py": None}, REPO: {INIT: None}})
    with open(file, "w", encoding="utf-8") as fout:
        fout.write(content)

    pyaud.git.add(".")
    pyaud.files.populate()
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(module)

    stderr = str(err.value)
    assert stderr == f"pyaud {module} did not pass all checks"
    assert "Path" not in stderr


@pytest.mark.usefixtures("init_remote")
def test_deploy_not_master(
    main: t.Any, monkeypatch: pytest.MonkeyPatch, nocolorcapsys: NoColorCapsys
) -> None:
    """Test that deployment is skipped when branch is not ``master``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setattr("pyaud.branch", lambda: "not_master")
    main("deploy-docs")
    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(
        i in out for i in ["Documentation not for master", PUSHING_SKIPPED]
    )


@pytest.mark.usefixtures("init_remote")
def test_deploy_master_not_set(
    main: t.Any, monkeypatch: pytest.MonkeyPatch, nocolorcapsys: NoColorCapsys
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
    main("deploy-docs")
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "The following is not set:",
            "- PYAUD_GH_NAME",
            "- PYAUD_GH_EMAIL",
            "- PYAUD_GH_TOKEN",
            PUSHING_SKIPPED,
        ]
    )


@pytest.mark.usefixtures("init_remote")
def test_deploy_master(
    main: t.Any, monkeypatch: pytest.MonkeyPatch, nocolorcapsys: NoColorCapsys
) -> None:
    """Test docs are properly deployed.

    Test for when environment variables are set and checked out at
    ``master``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
                            color codes.
    """
    project_dir = Path.cwd()
    readme = project_dir / README
    mock_plugins = pyaud.plugins.mapping()

    def _docs(*_: t.Any, **__: t.Any):
        Path(Path.cwd() / pyaud.environ.BUILDDIR / "html").mkdir(parents=True)

    mock_plugins["docs"] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    readme.touch()  # force stash
    pyaud.git.add(".")
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)

    with open(readme, "w", encoding="utf-8") as fout:
        fout.write(files.README_RST)

    main("deploy-docs", "--fix")
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "Pushing updated documentation",
            "Documentation Successfully deployed",
        ]
    )
    main("deploy-docs", "--fix")
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "No difference between local branch and remote",
            PUSHING_SKIPPED,
        ]
    )


@pytest.mark.parametrize(
    "rounds,expected",
    [
        (
            1,
            [
                "Pushing updated documentation",
                "Documentation Successfully deployed",
            ],
        ),
        (
            2,
            ["No difference between local branch and remote", PUSHING_SKIPPED],
        ),
    ],
    ids=["stashed", "multi"],
)
@pytest.mark.usefixtures("init_remote")
def test_deploy_master_param(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    rounds: int,
    expected: t.List[str],
) -> None:
    """Check that nothing happens when not checkout at master.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param rounds: How many times ``make_deploy_docs`` needs to be run.
    :param expected: Expected stdout result.
    """
    path = Path.cwd()
    mock_plugins = pyaud.plugins.mapping()

    def _docs(*_: t.Any, **__: t.Any) -> None:
        Path(path / pyaud.environ.BUILDDIR / "html").mkdir(parents=True)

    mock_plugins["docs"] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    with open(path / README, "w", encoding="utf-8") as fout:
        fout.write(files.README_RST)

    Path(path, FILES).touch()
    pyaud.git.add(".", devnull=True)
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)
    for _ in range(rounds):
        main("deploy-docs", "--fix")

    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(i in out for i in expected)


def test_deploy_cov_report_token(
    main: t.Any,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: t.Any,
) -> None:
    """Test ``make_deploy_cov`` when ``CODECOV_TOKEN`` is set.

    Test for when ``CODECOV_TOKEN`` is set and a coverage.xml file
    exists.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    Path(Path.cwd() / pyaud.environ.COVERAGE_XML).touch()
    patch_sp_print_called()
    monkeypatch.setenv("CODECOV_TOKEN", "token")
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["<Subprocess (codecov)>", "--file"])


def test_deploy_cov_no_token(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_deploy_cov``.

    Test for when ``CODECOV_TOKEN`` when only a coverage.xml file
    exists.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    Path(Path.cwd() / pyaud.environ.COVERAGE_XML).touch()
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert "CODECOV_TOKEN not set" in out


def test_deploy_cov_no_report_token(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_deploy_cov``.

     Test for when ``CODECOV_TOKEN`` is not set and a coverage.xml file
     does not. exist.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["No coverage report found"])


def test_make_format_success(
    main: t.Any, nocolorcapsys: NoColorCapsys, patch_sp_print_called: t.Any
) -> None:
    """Test ``Format`` when successful.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    pyaud.files.append(Path.cwd() / FILES)
    patch_sp_print_called()
    main("format")
    nocolorcapsys.readouterr()


def test_make_format_docs_fail(main: t.Any) -> None:
    """Test ``make_format`` when it fails.

    Ensure process fails when unformatted docstrings are found.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILES
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.files.append(path)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("format-docs")


def test_make_format_docs_suppress(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_format`` when running with ``-s/--suppress``.

    Ensure process announces it failed but does not actually return a
    non-zero exit-status.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILES
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    pyaud.files.append(path)
    main("format-docs", "--suppress")
    assert (
        nocolorcapsys.stderr().strip()
        == "Failed: returned non-zero exit status 3"
    )


def test_isort_and_black(main: t.Any) -> None:
    """Test ``AuditError`` is raised.

    For failed checks when looking for formatted inputs run through
    ``isort`` and ``Black``.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILES
    with open(path, "w", encoding="utf-8") as fout:
        fout.write(files.BEFORE_ISORT)

    pyaud.files.append(path)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("imports")


def test_isort_and_black_fix(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test file is correctly fixed  for failed check.

    When looking for formatted inputs run through ``isort`` and
    ``Black`` ensure no errors are raised, and output is as expected.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    with open(Path.cwd() / FILES, "w", encoding="utf-8") as fout:
        fout.write(files.BEFORE_ISORT)

    pyaud.files.append(Path.cwd() / FILES)
    main("imports", "--suppress", "--fix")
    out = nocolorcapsys.stdout()
    assert f"Fixed {Path(Path.cwd() / FILES).relative_to(Path.cwd())}" in out


def test_make_format_fix(main: t.Any) -> None:
    """Test ``make_format`` when it fails.

    :param main: Patch package entry point.
    """
    with open(Path.cwd() / FILES, "w", encoding="utf-8") as fout:
        fout.write(files.UNFORMATTED)

    pyaud.files.append(Path.cwd() / FILES)
    main("format", "--fix")
    with open(Path.cwd() / FILES, encoding="utf-8") as fin:
        assert fin.read().strip() == files.UNFORMATTED.replace("'", '"')


def test_make_unused_fix(
    main: t.Any, nocolorcapsys: NoColorCapsys, make_tree: t.Any
) -> None:
    """Test ``make_unused`` when ``-f/--fix`` is provided.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    package = Path.cwd() / "repo"
    make_tree(Path.cwd(), {"repo": {INIT: None}})
    file = package / FILES
    with open(file, "w", encoding="utf-8") as fout:
        fout.write(files.UNFORMATTED)  # also, an unused function

    pyaud.files.append(file)
    main("unused", "--fix")
    assert nocolorcapsys.stdout() == (
        "{}:1: unused function 'reformat_this' (60% confidence)\n"
        "Updating ``{}``\n"
        "created ``whitelist.py``\n"
        "Success: no issues found in 1 source files\n".format(
            file, Path.cwd() / pyaud.environ.WHITELIST
        )
    )
    with open(Path.cwd() / pyaud.environ.WHITELIST, encoding="utf-8") as fin:
        assert fin.read().strip() == (
            "reformat_this  # unused function (repo/file.py:1)"
        )


def test_make_unused_fail(main: t.Any) -> None:
    """Test ``make_unused`` with neither ``--fix`` or ``--suppress``.

    :param main: Patch package entry point.
    """
    with open(Path.cwd() / FILES, "w", encoding="utf-8") as fout:
        fout.write(files.UNFORMATTED)  # also, an unused function

    pyaud.files.append(Path.cwd() / FILES)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main("unused")

    assert str(err.value) == "pyaud unused did not pass all checks"


def test_make_format_docs_fix(
    main: t.Any, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_format`` when running with ``-f/--fix``.

    Ensure process fixes checked failure.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    pyaud.files.append(Path.cwd() / FILES)
    with open(Path.cwd() / FILES, "w", encoding="utf-8") as fout:
        fout.write(files.DOCFORMATTER_EXAMPLE)

    main("format-docs", "--fix")
    assert nocolorcapsys.stdout().strip() == NO_ISSUES


def test_format_str_fix(main: t.Any, nocolorcapsys: NoColorCapsys) -> None:
    """Test fix audit when f-strings can be created with ``flynt``.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    with open(Path.cwd() / FILES, "w", encoding="utf-8") as fout:
        fout.write(files.FORMAT_STR_FUNCS_PRE)

    pyaud.git.add(".", devnull=True)
    pyaud.files.populate()
    main("format-str", "--fix")
    nocolorcapsys.stdout()
    with open(Path.cwd() / FILES, encoding="utf-8") as fin:
        assert fin.read() == files.FORMAT_STR_FUNCS_POST


def test_audit_class_error(
    main: t.Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test errors are handled correctly when running ``pyaud audit``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILES)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("lint")


def test_no_exe_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default value for exe property.

    :param monkeypatch: Mock patch environment and attributes.
    """
    unique = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILES)

    # noinspection PyUnusedLocal
    @pyaud.plugins.register(name=unique)
    class Plugin(pyaud.plugins.Audit):
        """Nothing to do."""

        def audit(self, *args: t.Any, **kwargs: bool) -> int:
            """Nothing to do."""

    assert pyaud.plugins.get(unique).exe == []


def test_download_missing_stubs(
    monkeypatch: pytest.MonkeyPatch, main: t.Any
) -> None:
    """Test for coverage on missing stubs file.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :return:
    """
    path = Path(os.getcwd(), FILES)
    pyaud.files.append(path)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(
        SP_STDOUT, lambda _: ["error: Library stubs not installed for"]
    )
    main("typecheck")


def test_typecheck_re_raise_err(
    monkeypatch: pytest.MonkeyPatch, main: t.Any
) -> None:
    """Test for re-raise of error for non stub library errors.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :return:
    """
    path = Path(os.getcwd(), FILES)
    pyaud.files.append(path)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(SP_STDOUT, lambda _: [])
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main("typecheck")

    assert str(err.value) == "pyaud typecheck did not pass all checks"


def test_nested_toc(main: t.Any, make_tree: t.Any) -> None:
    """Test that only one file is completed with a nested project.

    Prior to this commit only ``repo.src.rst`` would be removed.
    This commit will remove any file and copy its contents to the
    single <NAME>.rst file e.g. ``repo.routes.rst`` is removed and
    ``repo.routes``, ``repo.routes.auth``, ``repo.routes.post``, and
    ``repo.routes.views`` is added to repo.rst.

    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(
        Path.cwd(),
        {
            "docs": {CONFPY: None},
            "repo": {
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
    main("toc")
    assert not Path(Path.cwd() / DOCS / "repo.routes.rst").is_file()
    with open(Path.cwd() / DOCS / f"{REPO}.rst", encoding="utf-8") as fin:
        assert fin.read() == EXPECTED_NESTED_TOC
