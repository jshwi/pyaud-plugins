"""
tests.fix_tests
===============
"""
from pathlib import Path

import pyaud
import pytest
import templatest

from pyaud_plugins import environ as ppe

from . import (
    FILE,
    FLAG_FIX,
    FORMAT,
    FORMAT_DOCS,
    FORMAT_STR,
    IMPORTS,
    NO_ISSUES,
    NO_ISSUES_ALL,
    TEST_FORMAT,
    UNUSED,
    MockMainType,
    NoColorCapsys,
    templates,
)


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
    pyaud.files.append(path)
    path.write_text(templates.BEFORE_ISORT, ppe.ENCODING)
    main(IMPORTS, FLAG_FIX)
    assert f"Fixed {FILE}" in nocolorcapsys.stdout()


def test_make_format_fix(main: MockMainType) -> None:
    """Test ``pyaud format`` when it fails.

    :param main: Patch package entry point.
    """
    template = templatest.templates.registered.getbyname(TEST_FORMAT)
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(template.template, ppe.ENCODING)
    main(FORMAT, FLAG_FIX)
    assert path.read_text(ppe.ENCODING) == template.expected


def test_make_unused_fix(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    nocolorcapsys: NoColorCapsys,
) -> None:
    """Test ``pyaud unused`` when ``-f/--fix`` is provided.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.Whitelist.cache_file",
        Path.cwd() / "whitelist.py",
    )
    template = templatest.templates.registered.getbyname(TEST_FORMAT)
    path = Path.cwd() / ppe.PACKAGE_NAME / FILE
    path.parent.mkdir()
    pyaud.files.append(path)
    path.write_text(template.template, ppe.ENCODING)
    main(UNUSED, FLAG_FIX)
    out = nocolorcapsys.stdout()
    unused_function = "reformat_this"
    assert unused_function in out
    assert "Success: no issues found in 1 source files" in out
    assert NO_ISSUES in out
    assert unused_function in ppe.WHITELIST.read_text(ppe.ENCODING)


def test_make_format_docs_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test ``pyaud format`` when running with ``-f/--fix``.

    Ensure process fixes checked failure.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(templates.DOCFORMATTER_EXAMPLE, ppe.ENCODING)
    main(FORMAT_DOCS, FLAG_FIX)
    assert NO_ISSUES_ALL in nocolorcapsys.stdout()


def test_format_str_fix(
    main: MockMainType, nocolorcapsys: NoColorCapsys
) -> None:
    """Test fix audit when f-strings can be created with ``flynt``.

    :param main: Patch package entry point.
    :param nocolorcapsys: Capture system output while stripping ANSI
        color codes.
    """
    template = templatest.templates.registered.getbyname("test-format-str")
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(template.template, ppe.ENCODING)
    main(FORMAT_STR, FLAG_FIX)
    nocolorcapsys.readouterr()
    assert template.expected in path.read_text(ppe.ENCODING)
