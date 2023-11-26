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
    templates,
)


def test_isort_and_black_fix(
    main: MockMainType, capfd: pytest.CaptureFixture
) -> None:
    """Test file is correctly fixed  for failed check.

    When looking for formatted inputs run through ``isort`` and
    ``Black`` ensure no errors are raised, and output is as expected.

    :param main: Patch package entry point.
    :param capfd: Capture file descriptor.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(templates.BEFORE_ISORT, "utf-8")
    main(IMPORTS, FLAG_FIX)
    std = capfd.readouterr()
    assert "Fixing" in std.out
    assert str(path) in std.out


def test_make_format_fix(main: MockMainType) -> None:
    """Test ``pyaud format`` when it fails.

    :param main: Patch package entry point.
    """
    template = templatest.templates.registered.getbyname(TEST_FORMAT)
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(template.template, "utf-8")  # type: ignore
    main(FORMAT, FLAG_FIX)
    assert path.read_text("utf-8") == template.expected  # type: ignore


def test_make_unused_fix(
    monkeypatch: pytest.MonkeyPatch,
    main: MockMainType,
    capfd: pytest.CaptureFixture,
) -> None:
    """Test ``pyaud unused`` when ``-f/--fix`` is provided.

    :param monkeypatch: Mock patch environment and attributes.
    :param main: Patch package entry point.
    :param capfd: Capture file descriptor.
    """
    monkeypatch.setattr(
        "pyaud_plugins._plugins.write.Whitelist.cache_file",
        Path.cwd() / "whitelist.py",
    )
    template = templatest.templates.registered.getbyname(TEST_FORMAT)
    path = Path.cwd() / ppe.PACKAGE_NAME / FILE
    path.parent.mkdir()
    pyaud.files.append(path)
    path.write_text(template.template, "utf-8")  # type: ignore
    main(UNUSED, FLAG_FIX)
    std = capfd.readouterr()
    unused_function = "reformat_this"
    assert unused_function in std.out
    assert "Success: no issues found in 1 source files" in std.out
    assert NO_ISSUES in std.out
    assert unused_function in ppe.WHITELIST.read_text("utf-8")


def test_make_format_docs_fix(
    main: MockMainType, capsys: pytest.CaptureFixture
) -> None:
    """Test ``pyaud format`` when running with ``-f/--fix``.

    Ensure process fixes checked failure.

    :param main: Patch package entry point.
    :param capsys: Capture sys out.
    """
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(templates.DOCFORMATTER_EXAMPLE, "utf-8")
    main(FORMAT_DOCS, FLAG_FIX)
    std = capsys.readouterr()
    assert NO_ISSUES_ALL in std.out


def test_format_str_fix(
    main: MockMainType, capsys: pytest.CaptureFixture
) -> None:
    """Test fix audit when f-strings can be created with ``flynt``.

    :param main: Patch package entry point.
    :param capsys: Capture sys out.
    """
    template = templatest.templates.registered.getbyname("test-format-str")
    path = Path.cwd() / FILE
    pyaud.files.append(path)
    path.write_text(template.template, "utf-8")  # type: ignore
    main(FORMAT_STR, FLAG_FIX)
    capsys.readouterr()
    assert template.expected in path.read_text("utf-8")  # type: ignore
