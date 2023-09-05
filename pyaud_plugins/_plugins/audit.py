"""
pyaud_plugins._plugins.audit
============================
"""
import subprocess

import pyaud


@pyaud.plugins.register()
class Lint(pyaud.plugins.Audit):
    """Lint code with ``pylint``."""

    cache = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["pylint", "--output-format=colorized", *pyaud.files.args()],
            check=True,
        ).returncode


@pyaud.plugins.register()
class Typecheck(pyaud.plugins.Audit):
    """Typecheck code with ``mypy``.

    Check there are no errors between the files and their stub-files.
    """

    cache = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        mypy = "mypy"
        check = not kwargs.get("suppress", False)
        # ignore the first error that might occur
        # capture output to analyse for missing stub libraries
        result = subprocess.run(
            [mypy, "--ignore-missing-imports", *pyaud.files.args()],
            text=True,
            capture_output=True,
            check=False,
        )

        # if no error occurred, continue on to print message and return
        # value
        if result.returncode:
            # if error occurred it might be because the stub library is
            # not installed: automatically download and install stub
            # library if the below message occurred
            if "error: Library stubs not installed for" in result.stdout:
                subprocess.run(
                    [mypy, "--non-interactive", "--install-types"], check=check
                )

                # continue on to run the first command again, which will
                # not, by default, ignore any consecutive errors
                # do not capture output again
                return subprocess.run(
                    [
                        mypy,
                        "--ignore-missing-imports",
                        *pyaud.files.args(),
                        *args,
                    ],
                    check=check,
                ).returncode

            # if any error occurred that wasn't because of a missing
            # stub library
            print(result.stdout)
            return 1

        print(result.stdout)
        return result.returncode


@pyaud.plugins.register()
class Const(pyaud.plugins.Audit):
    """Check code for repeat use of strings."""

    cache = True
    cache_all = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["constcheck", *pyaud.files.args()], check=True
        ).returncode


@pyaud.plugins.register()
class Params(pyaud.plugins.Audit):
    """Check docstring params match function signatures."""

    cache = True
    cache_all = True

    def audit(self, *args: str, **kwargs: bool) -> int:
        return subprocess.run(
            ["docsig", *pyaud.files.args()], check=True
        ).returncode
