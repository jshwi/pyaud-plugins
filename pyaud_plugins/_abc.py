"""
pyaud_plugins._abc
==================
"""
from __future__ import annotations

import typing as _t
from abc import abstractmethod as _abstractmethod

import pyaud as _pyaud


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
