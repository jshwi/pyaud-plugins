"""
pyaud_plugins._plugins.audit
============================
"""
import sys
import typing as t

import pyaud

from pyaud_plugins._abc import ColorAudit


@pyaud.plugins.register()
class Lint(ColorAudit):
    """Lint code with ``pylint``."""

    pylint = "pylint"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.pylint]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.pylint].call(
            "--output-format=colorized", *args, *pyaud.files.args(), **kwargs
        )


@pyaud.plugins.register()
class Typecheck(pyaud.plugins.Audit):
    """Typecheck code with ``mypy``.

    Check that there are no errors between the files and their stub-
    files.
    """

    mypy = "mypy"
    cache = True

    @property
    def exe(self) -> t.List[str]:
        return [self.mypy]

    def audit(self, *args: str, **kwargs: bool) -> int:
        # save the value of ``suppress`` if it exists: default to False
        suppress = kwargs.get("suppress", False)

        # ignore the first error that might occur
        # capture output to analyse for missing stub libraries
        kwargs["suppress"] = True
        returncode = self.subprocess[self.mypy].call(
            "--ignore-missing-imports",
            *pyaud.files.args(),
            *args,
            capture=True,
            **kwargs,
        )

        # restore value of ``suppress``
        kwargs["suppress"] = suppress
        stdout = self.subprocess[self.mypy].stdout()

        # if no error occurred, continue on to print message and return
        # value
        if returncode:
            # if error occurred it might be because the stub library is
            # not installed: automatically download and install stub
            # library if the below message occurred
            if any(
                "error: Library stubs not installed for" in i for i in stdout
            ):
                self.subprocess[self.mypy].call(
                    "--non-interactive", "--install-types"
                )

                # continue on to run the first command again, which will
                # not, by default, ignore any consecutive errors
                # do not capture output again
                return self.subprocess[self.mypy].call(
                    "--ignore-missing-imports",
                    *pyaud.files.args(),
                    *args,
                    **kwargs,
                )

            # if any error occurred that wasn't because of a missing
            # stub library
            print("\n".join(stdout))
            if not suppress:
                raise pyaud.exceptions.AuditError(" ".join(sys.argv))

        else:
            print("\n".join(stdout))

        return returncode


@pyaud.plugins.register()
class Const(ColorAudit):
    """Check code for repeat use of strings."""

    constcheck = "constcheck"
    cache = True
    cache_all = True

    @property
    def exe(self) -> t.List[str]:
        return [self.constcheck]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.constcheck].call(*pyaud.files.args())


@pyaud.plugins.register()
class Params(ColorAudit):
    """Check docstring params match function signatures."""

    docsig = "docsig"
    cache = True
    cache_all = True

    @property
    def exe(self) -> t.List[str]:
        return [self.docsig]

    def audit(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.docsig].call(*pyaud.files.args())
