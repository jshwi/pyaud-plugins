"""
tests._test
===========
"""
# pylint: disable=too-many-lines,too-many-arguments,cell-var-from-loop
# pylint: disable=too-few-public-methods,protected-access
import datetime
import typing as t
from pathlib import Path

import pyaud
import pytest

import pyaud_plugins as pplugins
from pyaud_plugins import environ as ppe

from . import (
    CONST,
    COVERAGE,
    DEPLOY_COV,
    DEPLOY_DOCS,
    FILE,
    FLAG_FIX,
    FLAG_SUPPRESS,
    FORMAT,
    FORMAT_DOCS,
    FORMAT_STR,
    IMPORTS,
    INIT,
    INIT_REMOTE,
    INITIAL_COMMIT,
    NO_ISSUES,
    NO_TESTS_FOUND,
    PUSHING_SKIPPED,
    PYAUD_FILES_POPULATE,
    PYAUD_PLUGINS_PLUGINS,
    REQUIREMENTS,
    SP_CALL,
    SP_OPEN_PROC,
    SP_REPR_PYTEST,
    SP_STDOUT,
    TOC,
    TYPECHECK,
    UNUSED,
    WHITELIST,
    MakeTreeType,
    MockCallStatusType,
    MockMainType,
    MockSPOutputType,
    MockSPPrintCalledType,
    NoColorCapsys,
    templates,
)


def test_no_files_found(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test the correct output is produced when no file exists.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main(TYPECHECK)
    assert nocolorcapsys.stdout().strip() == "No files found"


@pytest.mark.parametrize(
    "contents,expected",
    [
        (["created"], f"created ``{ppe.WHITELIST.name}``"),
        (["", "updated"], f"updated ``{ppe.WHITELIST.name}``"),
        (
            ["up-to-date", "up-to-date"],
            f"``{ppe.WHITELIST.name}`` is already up to date",
        ),
    ],
    ids=("created", "updated", "up_to_date"),
)
def test_write_command(
    main: MockMainType,
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

        def mock_write_whitelist(*_: str, **__: bool) -> None:
            with open(
                Path.cwd() / ppe.WHITELIST, "w", encoding=ppe.ENCODING
            ) as fout:
                fout.write(content)

        monkeypatch.setattr(
            "pyaud_plugins.modules.Whitelist.write", mock_write_whitelist
        )
        main(WHITELIST)

    assert expected in nocolorcapsys.stdout()


@pytest.mark.parametrize(
    "is_tests,expected", [(False, "No coverage to report"), (True, "xml")]
)
def test_call_coverage_xml(
    main: MockMainType,
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
        def call(cls, *args: str, **_: bool) -> int:
            """Print the args passed to the subprocess object.

            :param args: Args to print.
            :param _: Unused misc kwargs.
            """
            print(*args)
            return 0

    class _Tests(pplugins.modules.Tests):
        @property
        def is_tests(self) -> bool:
            return is_tests

        def action(self, *args: str, **kwargs: bool) -> int:
            return 0

    monkeypatch.setattr(
        "pyaud.plugins._SubprocessFactory", lambda *_: {COVERAGE: _HasCall}
    )
    pplugins.modules.Coverage.__bases__ = (_Tests,)
    del pyaud.plugins._plugins[COVERAGE]
    pyaud.plugins._plugins[COVERAGE] = pplugins.modules.Coverage
    main(COVERAGE)
    assert nocolorcapsys.stdout().strip() == expected


def test_make_deploy_all(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    call_status: MockCallStatusType,
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
    modules = DEPLOY_COV, DEPLOY_DOCS
    mocked_plugins = pyaud.plugins.mapping()
    for module in modules:
        mocked_plugins[module] = call_status(module)  # type: ignore

    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    main("deploy")
    out = nocolorcapsys.stdout().splitlines()
    for module in modules:
        assert f"{pyaud.__name__} {module}" in out


def test_make_deploy_all_fail(
    main: MockMainType,
    call_status: MockCallStatusType,
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
    mock_plugins = pyaud.plugins.mapping()
    mock_plugins[DEPLOY_DOCS] = call_status(DEPLOY_DOCS, 1)  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    main("deploy")
    out = nocolorcapsys.stdout().splitlines()
    assert f"{pyaud.__name__} {DEPLOY_DOCS}" in out


def test_make_docs_no_docs(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test correct message is produced.

    Test when running ``pyaud docs`` when no docs are present.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    Path(Path.cwd() / FILE).touch()
    main(ppe.DOCS.name)
    assert nocolorcapsys.stdout().strip() == "No docs found"


def test_make_docs_toc_fail(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    make_tree: MakeTreeType,
) -> None:
    """Test that error message is produced when ``make_toc`` fails.

    Test process stops when ``make_toc`` fails before running the main
    ``make_docs`` process.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(Path.cwd(), {ppe.DOCS.name: {ppe.DOCS_CONF.name: None}})
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(ppe.DOCS.name)

    assert str(err.value) == "pyaud docs did not pass all checks"


def test_make_docs_rm_cache(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    call_status: MockCallStatusType,
    make_tree: MakeTreeType,
) -> None:
    """Test ``make_docs`` removes all builds before starting a new one.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param call_status: Patch function to return specific exit-code.
    :param make_tree: Create directory tree from dict mapping.
    """
    # disable call to ``Subprocess`` to only create ./docs/_build
    # directory so tests can continue
    def _call(*_: str, **__: bool) -> int:
        ppe.BUILDDIR.mkdir(parents=True)
        return 0

    # patch ``make_toc`` and ``Subprocess.call``
    mocked_plugins = pyaud.plugins.mapping()
    mocked_plugins[TOC] = call_status(TOC)  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_plugins)
    monkeypatch.setattr(SP_CALL, _call)
    make_tree(
        Path.cwd(),
        {ppe.DOCS.name: {ppe.DOCS_CONF.name: None, "readme.rst": None}},
    )
    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.README_RST)

    ppe.BUILDDIR.mkdir(parents=True)
    Path(ppe.BUILDDIR / "marker").touch()
    freeze_docs_build = ppe.BUILDDIR.iterdir()

    # to test creation of README.rst content needs to be written to file
    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.README_RST)

    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(ppe.DOCS.name)
    assert freeze_docs_build != ppe.BUILDDIR.iterdir()


def test_make_files(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    call_status: MockCallStatusType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test correct commands are executed when running ``make_files``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    :param call_status: Patch function to return specific exit-code.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    file_funcs = REQUIREMENTS, TOC, WHITELIST
    mocked_modules = pyaud.plugins.mapping()
    for file_func in file_funcs:
        mocked_modules[file_func] = call_status(file_func)  # type: ignore

    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mocked_modules)

    main("files")
    assert (
        nocolorcapsys.stdout()
        == "\npyaud requirements\n\npyaud toc\n\npyaud whitelist\n"
    )


def test_make_format(main: MockMainType) -> None:
    """Test ``make_format`` when successful and when it fails.

    :param main: Patch package entry point.
    """
    file = Path.cwd() / FILE
    with open(file, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.UNFORMATTED)

    pyaud.files.append(file)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(FORMAT)


def test_pipfile2req_commands(
    main: MockMainType,
    patch_sp_print_called: MockSPPrintCalledType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test that the correct commands are executed.

    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    with open(ppe.PIPFILE_LOCK, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.PIPFILE_LOCK)

    patch_sp_print_called()
    main(REQUIREMENTS)
    out = nocolorcapsys.stdout()
    assert all(
        e in out
        for e in (
            f"Updating ``{ppe.REQUIREMENTS}``",
            f"<Subprocess (pipfile2req)> {ppe.PIPFILE_LOCK}",
            f"<Subprocess (pipfile2req)> {ppe.PIPFILE_LOCK} --dev",
            f"created ``{ppe.REQUIREMENTS.name}``",
        )
    )


def test_readme_replace() -> None:
    """Test that ``LineSwitch`` properly edits a file."""

    def _test_file_index(title: str, underline: str) -> None:
        with open(ppe.README_RST, encoding=ppe.ENCODING) as fin:
            lines = fin.read().splitlines()

        assert lines[0] == title
        assert lines[1] == len(underline) * "="

    repo_underline = len(ppe.PACKAGE_NAME) * "="
    readme_underline = len(ppe.README_RST.stem) * "="
    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(f"{ppe.PACKAGE_NAME}\n{repo_underline}\n")

    _test_file_index(ppe.PACKAGE_NAME, repo_underline)
    with pyaud.parsers.LineSwitch(
        ppe.README_RST, {0: ppe.README_RST.stem, 1: readme_underline}
    ):
        _test_file_index(ppe.README_RST.stem, readme_underline)

    _test_file_index(ppe.PACKAGE_NAME, repo_underline)


def test_append_whitelist(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
) -> None:
    """Test that whitelist file argument is appended ``vulture`` call.

    Test for when whitelist.py exists and is not appended if it does
    not, thus avoiding an error.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    Path(Path.cwd() / FILE).touch()
    ppe.WHITELIST.touch()
    pyaud.git.add(".")
    pyaud.files.populate()
    patch_sp_print_called()
    main(UNUSED)
    assert str(ppe.WHITELIST) in nocolorcapsys.stdout()


def test_mypy_expected(
    main: MockMainType,
    patch_sp_print_called: MockSPPrintCalledType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test that the ``mypy`` command is correctly called.

    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    patch_sp_print_called()
    main(TYPECHECK)
    assert (
        f"<Subprocess (mypy)> --ignore-missing-imports {path}"
        in nocolorcapsys.stdout()
    )


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
        announce what is called`
    :param relpath: Relative path to file.
    :param expected: Expected stdout.
    """
    pyaud.files.append(Path.cwd() / relpath)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    patch_sp_print_called()
    main(ppe.TESTS.name)
    assert nocolorcapsys.stdout().strip() == expected


def test_make_toc(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    patch_sp_print_called: MockSPPrintCalledType,
    make_tree: MakeTreeType,
) -> None:
    """Test that the default toc file is edited correctly.

    Ensure additional files generated by ``sphinx-api`` doc are removed.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    :param make_tree: Create directory tree from dict mapping.
    """
    modules = "modules.rst"
    make_tree(
        Path.cwd(), {ppe.DOCS.name: {modules: None, ppe.DOCS_CONF: None}}
    )
    with open(ppe.PACKAGE_TOC, "w", encoding=ppe.ENCODING) as fout:
        assert fout.write(templates.DEFAULT_TOC)

    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    patch_sp_print_called()
    main(TOC)
    with open(ppe.PACKAGE_TOC, encoding=ppe.ENCODING) as fin:
        assert fin.read() == templates.ALTERED_TOC

    assert not Path(ppe.DOCS / modules).is_file()


def test_make_requirements(
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
    with open(ppe.PIPFILE_LOCK, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.PIPFILE_LOCK)

    patch_sp_output(templates.PIPFILE2REQ_PROD, templates.PIPFILE2REQ_DEV)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    main(REQUIREMENTS)
    assert nocolorcapsys.stdout() == (
        "Updating ``{}``\ncreated ``{}``\n".format(
            ppe.REQUIREMENTS, ppe.REQUIREMENTS.name
        )
    )
    with open(ppe.REQUIREMENTS, encoding=ppe.ENCODING) as fin:
        assert fin.read() == templates.REQUIREMENTS


def test_make_whitelist(
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    make_tree: MakeTreeType,
) -> None:
    """Test a whitelist.py file is created properly.

    Test for when piping data from ``vulture --make-whitelist``.

    :param monkeypatch: Mock patch environment and attributes.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param make_tree: Create directory tree from dict mapping.
    """
    make_tree(
        Path.cwd(),
        {
            ppe.TESTS.name: {"conftest.py": None, FILE: None},
            "pyaud": {"src": {INIT: None, "modules.py": None}},
        },
    )
    pyaud.git.init(devnull=True)
    pyaud.git.add(".")
    pyaud.files.populate()
    monkeypatch.setattr(
        "spall.Subprocess.stdout", lambda *_, **__: templates.Whitelist.be8a443
    )
    pyaud.plugins.get(WHITELIST)()
    assert nocolorcapsys.stdout() == (
        f"Updating ``{ppe.WHITELIST}``\ncreated ``{ppe.WHITELIST.name}``\n"
    )
    with open(ppe.WHITELIST, encoding=ppe.ENCODING) as fin:
        assert fin.read() == templates.Whitelist.be8a443_all()


def test_pylint_colorized(
    main: MockMainType, capsys: pytest.CaptureFixture
) -> None:
    """Test that color codes are produced with ``process.PIPE``.

    Test ``pylint --output-format=colorized``. If ``colorama`` is
    installed and a process calls ``colorama.init()`` a process pipe
    will be stripped. Using environment variable ``PYCHARM_HOSTED`` for
    now as a workaround as this voids this action.

    :param main: Patch package entry point.
    :param capsys: Capture sys output.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write("import this_package_does_not_exist")

    pyaud.files.append(path)
    main("lint", FLAG_SUPPRESS)
    output = capsys.readouterr()[0]
    assert all(
        i in output
        for i in ["\x1b[7;33m", "\x1b[0m", "\x1b[1m", "\x1b[1;31m", "\x1b[35m"]
    )


def test_isort_imports(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test isort properly sorts file imports.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.IMPORTS_UNSORTED)

    pyaud.files.append(path)
    main(IMPORTS, FLAG_FIX)
    with open(path, encoding=ppe.ENCODING) as fin:
        assert (
            templates.IMPORTS_SORTED.splitlines()[1:]
            == fin.read().splitlines()[:20]
        )

    out = nocolorcapsys.stdout()
    assert all(i in out for i in (f"Fixed {path.name}", NO_ISSUES))
    main(IMPORTS)


def test_readme(main: MockMainType, nocolorcapsys: NoColorCapsys) -> None:
    """Test standard README and return values.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main("readme")
    assert (
        nocolorcapsys.stdout().strip() == "No README.rst found in project root"
    )
    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.CODE_BLOCK_TEMPLATE)

    main("readme")
    assert (
        "\n".join([i.strip() for i in nocolorcapsys.stdout().splitlines()])
        == templates.CODE_BLOCK_EXPECTED
    )


@pytest.mark.parametrize(
    "module,content",
    [
        (FORMAT, templates.UNFORMATTED),
        (IMPORTS, templates.IMPORTS_UNSORTED),
        (FORMAT_STR, templates.FORMAT_STR_FUNCS_PRE),
        (FORMAT_DOCS, templates.DOCFORMATTER_EXAMPLE),
    ],
    ids=[FORMAT, IMPORTS, FORMAT_STR, FORMAT_DOCS],
)
def test_py_audit_error(
    main: MockMainType, make_tree: MakeTreeType, module: str, content: str
) -> None:
    """Test ``AuditError`` message.

    :param main: Patch package entry point.
    :param make_tree: Create directory tree from dict mapping.
    :param module: [<module>].__name__.
    :param content: Content to write to file.
    """
    file = Path.cwd() / FILE
    make_tree(
        Path.cwd(),
        {ppe.TESTS.name: {"_test.py": None}, ppe.PACKAGE_NAME: {INIT: None}},
    )
    with open(file, "w", encoding=ppe.ENCODING) as fout:
        fout.write(content)

    pyaud.git.add(".")
    pyaud.files.populate()
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(module)

    stderr = str(err.value)
    assert stderr == f"pyaud {module} did not pass all checks"
    assert "Path" not in stderr


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
    monkeypatch.setattr("pyaud.branch", lambda: "not_master")
    main(DEPLOY_DOCS)
    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(
        i in out for i in ["Documentation not for master", PUSHING_SKIPPED]
    )


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
    mock_plugins = pyaud.plugins.mapping()

    def _docs(*_: str, **__: int) -> int:
        Path(Path.cwd() / ppe.BUILDDIR / "html").mkdir(parents=True)
        return 0

    mock_plugins[ppe.DOCS.name] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    ppe.README_RST.touch()  # force stash
    pyaud.git.add(".")
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)

    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.README_RST)

    main(DEPLOY_DOCS, FLAG_FIX)
    out = nocolorcapsys.stdout().splitlines()
    assert all(
        i in out
        for i in [
            "Pushing updated documentation",
            "Documentation Successfully deployed",
        ]
    )
    main(DEPLOY_DOCS, FLAG_FIX)
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
@pytest.mark.usefixtures(INIT_REMOTE)
def test_deploy_master_param(
    main: MockMainType,
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
    mock_plugins = pyaud.plugins.mapping()

    def _docs(*_: str, **__: bool) -> int:
        Path(ppe.BUILDDIR / "html").mkdir(parents=True)
        return 0

    mock_plugins[ppe.DOCS.name] = _docs  # type: ignore
    monkeypatch.setattr(PYAUD_PLUGINS_PLUGINS, mock_plugins)
    with open(ppe.README_RST, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.README_RST)

    Path(Path.cwd(), FILE).touch()
    pyaud.git.add(".", devnull=True)
    pyaud.git.commit("-m", INITIAL_COMMIT, devnull=True)
    for _ in range(rounds):
        main(DEPLOY_DOCS, FLAG_FIX)

    out = [i.strip() for i in nocolorcapsys.stdout().splitlines()]
    assert all(i in out for i in expected)


def test_deploy_cov_report_token(
    main: MockMainType,
    monkeypatch: pytest.MonkeyPatch,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
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
    ppe.COVERAGE_XML.touch()
    patch_sp_print_called()
    monkeypatch.setenv("CODECOV_TOKEN", "token")
    main("deploy-cov")
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["<Subprocess (codecov)>", "--file"])


def test_deploy_cov_no_token(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_deploy_cov``.

    Test for when ``CODECOV_TOKEN`` when only a coverage.xml file
    exists.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    ppe.COVERAGE_XML.touch()
    main(DEPLOY_COV)
    out = nocolorcapsys.stdout()
    assert "CODECOV_TOKEN not set" in out


def test_deploy_cov_no_report_token(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_deploy_cov``.

     Test for when ``CODECOV_TOKEN`` is not set and a coverage.xml file
     does not. exist.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    main(DEPLOY_COV)
    out = nocolorcapsys.stdout()
    assert all(e in out for e in ["No coverage report found"])


def test_make_format_success(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
) -> None:
    """Test ``Format`` when successful.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    pyaud.files.append(Path.cwd() / FILE)
    patch_sp_print_called()
    main(FORMAT)
    nocolorcapsys.readouterr()


def test_make_format_docs_fail(main: MockMainType) -> None:
    """Test ``make_format`` when it fails.

    Ensure process fails when unformatted docstrings are found.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.DOCFORMATTER_EXAMPLE)

    pyaud.files.append(path)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(FORMAT_DOCS)


def test_make_format_docs_suppress(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_format`` when running with ``-s/--suppress``.

    Ensure process announces it failed but does not actually return a
    non-zero exit-status.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.DOCFORMATTER_EXAMPLE)

    pyaud.files.append(path)
    main(FORMAT_DOCS, FLAG_SUPPRESS)
    assert (
        nocolorcapsys.stderr().strip()
        == "Failed: returned non-zero exit status 3"
    )


def test_isort_and_black(main: MockMainType) -> None:
    """Test ``AuditError`` is raised.

    For failed checks when looking for formatted inputs run through
    ``isort`` and ``Black``.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.BEFORE_ISORT)

    pyaud.files.append(path)
    with pytest.raises(pyaud.exceptions.AuditError):
        main(IMPORTS)


def test_isort_and_black_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test file is correctly fixed  for failed check.

    When looking for formatted inputs run through ``isort`` and
    ``Black`` ensure no errors are raised, and output is as expected.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.BEFORE_ISORT)

    pyaud.files.append(path)
    main(IMPORTS, FLAG_SUPPRESS, FLAG_FIX)
    out = nocolorcapsys.stdout()
    assert f"Fixed {path.relative_to(Path.cwd())}" in out


def test_make_format_fix(main: MockMainType) -> None:
    """Test ``make_format`` when it fails.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.UNFORMATTED)

    pyaud.files.append(path)
    main(FORMAT, FLAG_FIX)
    with open(path, encoding=ppe.ENCODING) as fin:
        assert fin.read().strip() == templates.UNFORMATTED.replace("'", '"')


def test_make_unused_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys, make_tree: MakeTreeType
) -> None:
    """Test ``make_unused`` when ``-f/--fix`` is provided.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    make_tree(Path.cwd(), {ppe.PACKAGE_NAME: {INIT: None}})
    file = Path.cwd() / ppe.PACKAGE_NAME / FILE
    with open(file, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.UNFORMATTED)  # also, an unused function

    pyaud.files.append(file)
    main(UNUSED, FLAG_FIX)
    assert nocolorcapsys.stdout() == (
        "{}:1: unused function 'reformat_this' (60% confidence)\n"
        "Updating ``{}``\n"
        "created ``whitelist.py``\n"
        "Success: no issues found in 1 source files\n".format(
            file, ppe.WHITELIST
        )
    )
    with open(ppe.WHITELIST, encoding=ppe.ENCODING) as fin:
        assert fin.read().strip() == (
            "reformat_this  # unused function (package/file.py:1)"
        )


def test_make_unused_fail(main: MockMainType) -> None:
    """Test ``make_unused`` with neither ``--fix`` or ``--suppress``.

    :param main: Patch package entry point.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.UNFORMATTED)  # also, an unused function

    pyaud.files.append(path)
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(UNUSED)

    assert str(err.value) == "pyaud unused did not pass all checks"


def test_make_format_docs_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``make_format`` when running with ``-f/--fix``.

    Ensure process fixes checked failure.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.DOCFORMATTER_EXAMPLE)

    main(FORMAT_DOCS, FLAG_FIX)
    assert nocolorcapsys.stdout().strip() == NO_ISSUES


def test_format_str_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test fix audit when f-strings can be created with ``flynt``.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    with open(path, "w", encoding=ppe.ENCODING) as fout:
        fout.write(templates.FORMAT_STR_FUNCS_PRE)

    pyaud.git.add(".", devnull=True)
    pyaud.files.populate()
    main(FORMAT_STR, FLAG_FIX)
    nocolorcapsys.stdout()
    with open(path, encoding=ppe.ENCODING) as fin:
        assert fin.read() == templates.FORMAT_STR_FUNCS_POST


def test_audit_class_error(
    main: MockMainType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test errors are handled correctly when running ``pyaud audit``.

    :param main: Patch package entry point.
    :param monkeypatch: Mock patch environment and attributes.
    """
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(PYAUD_FILES_POPULATE, lambda: None)
    with pytest.raises(pyaud.exceptions.AuditError):
        main("lint")


def test_no_exe_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default value for exe property.

    :param monkeypatch: Mock patch environment and attributes.
    """
    unique = datetime.datetime.now().strftime("%d%m%YT%H%M%S")
    monkeypatch.setattr(SP_OPEN_PROC, lambda *_, **__: 1)
    pyaud.files.append(Path.cwd() / FILE)

    class Plugin(pyaud.plugins.Audit):
        """Nothing to do."""

        def audit(self, *args: str, **kwargs: bool) -> int:
            """Nothing to do."""

    pyaud.plugins.register(name=unique)(Plugin)
    assert pyaud.plugins.get(unique).exe == []


def test_download_missing_stubs(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test for coverage on missing stubs file.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :return:
    """
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(
        SP_STDOUT, lambda _: ["error: Library stubs not installed for"]
    )
    main(TYPECHECK)


def test_typecheck_re_raise_err(
    monkeypatch: pytest.MonkeyPatch, main: MockMainType
) -> None:
    """Test for re-raise of error for non stub library errors.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :return:
    """
    pyaud.files.append(Path.cwd() / FILE)
    monkeypatch.setattr(SP_CALL, lambda *_, **__: 1)
    monkeypatch.setattr(SP_STDOUT, lambda _: [])
    with pytest.raises(pyaud.exceptions.AuditError) as err:
        main(TYPECHECK)

    assert str(err.value) == "pyaud typecheck did not pass all checks"


def test_nested_toc(main: MockMainType, make_tree: MakeTreeType) -> None:
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
    assert not Path(ppe.DOCS / "repo.routes.rst").is_file()
    with open(ppe.PACKAGE_TOC, encoding=ppe.ENCODING) as fin:
        assert fin.read() == templates.EXPECTED_NESTED_TOC


def test_sphinx_build_abc(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
) -> None:
    """Test args properly passed to ``SphinxBuild``'s ``action``.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    # noinspection PyUnresolvedReferences
    class SphinxBuild(pplugins._abc.SphinxBuild):
        """SphinxBuild ABC."""

        @property
        def args(self) -> t.Tuple[t.Union[str, Path], ...]:
            return "testing", "args", "passed", "to", "sphinx-build"

    patch_sp_print_called()
    pyaud.plugins.register()(SphinxBuild)
    main("sphinx-build")
    out = nocolorcapsys.stdout().splitlines()
    assert (
        "<Subprocess (sphinx-build)> testing args passed to sphinx-build"
        in out
    )


def test_call_const(
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
    patch_sp_print_called: MockSPPrintCalledType,
) -> None:
    """Test register and call of ``const`` plugin.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    :param patch_sp_print_called: Patch ``Subprocess.call`` to only
        announce what is called.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    patch_sp_print_called()
    main(CONST)
    out = nocolorcapsys.stdout().splitlines()
    assert f"<Subprocess (constcheck)> {path}" in out
    assert "Success: no issues found in 1 source files" in out
