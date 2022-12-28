"""Plugin package for Pyaud."""
from . import _plugins  # noqa
from ._environ import environ
from ._version import __version__

__all__ = ["__version__", "environ"]
