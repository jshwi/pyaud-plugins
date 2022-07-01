"""
pyaud_plugins._abc
==================
"""
from __future__ import annotations

import os as _os
import typing as _t
from abc import abstractmethod as _abstractmethod

import pyaud as _pyaud


class CheckFix(_pyaud.plugins.FixAll):
    """Subclass for ``Fix`` plugins that check files and edit in place.

    Utilize the ``--check`` and ``--in-place`` flags.
    """

    check = "--check"
    in_place = "--in-place"

    @property
    def args(self) -> _t.Tuple[str | _os.PathLike, ...]:
        """Default args to include with subclass."""
        return ()

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            self.check, *_pyaud.files.args(), *self.args, *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            self.in_place, *_pyaud.files.args(), *self.args, *args, **kwargs
        )


class SphinxBuild(_pyaud.plugins.Action):
    """Subclass for ``Action`` classes using ``sphinx-build``."""

    @property
    def exe(self) -> _t.List[str]:
        return ["sphinx-build"]

    def sphinx_build(self, *args: str, **kwargs: bool) -> int:
        """``sphinx-build`` executable ready to go.

        :param args: Args to pass to subprocess.
        :param kwargs: Kwargs to pass to subprocess.
        :return: Returncode.
        """
        return self.subprocess[self.exe[0]].call(*self.args, *args, **kwargs)

    @property
    @_abstractmethod
    def args(self) -> _t.Tuple[str | _os.PathLike, ...]:
        """Args for ``sphinx-build``."""

    def action(self, *args: str, **kwargs: bool) -> int:
        return self.sphinx_build(*args, **kwargs)


class ColorAudit(_pyaud.plugins.Audit):
    """Instantiate with ``PYCHARM_HOSTED`` as ``True``."""

    @property
    def env(self) -> _t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    @_abstractmethod
    def exe(self) -> _t.List[str]:
        """List of executables to add to ``subprocess`` dict."""

    @_abstractmethod
    def audit(self, *args: str, **kwargs: bool) -> int:
        """All audit logic to be written within this method.

        :param args: Args to pass to subprocess.
        :param kwargs: Kwargs to pass to subprocess.
        :return: Returncode.
        """
