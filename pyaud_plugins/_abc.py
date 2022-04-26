"""
pyaud_plugins._abc
==================
"""
import pyaud as _pyaud


class CheckFix(_pyaud.plugins.Fix):
    """Subclass for ``Fix`` plugins that check files and edit in place.

    Utilize the ``--check`` and ``--in-place`` flags.
    """

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            "--check", *_pyaud.files.args(), *args, **kwargs
        )

    def fix(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.exe[0]].call(
            "--in-place", *_pyaud.files.args(), *args, **kwargs
        )
