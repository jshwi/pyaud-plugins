"""
pyaud_plugins_plugins.deprecate
===============================
"""
import os
import shutil
import typing as t
from pathlib import Path

import pyaud

from pyaud_plugins._environ import environ as e
from pyaud_plugins._utils import colors, git

HEAD = "HEAD"


def branch() -> t.Optional[str]:
    """Return current Git branch if in Git repository.

    :return: Checked out branch or None if no parent commit or repo.
    """
    git.symbolic_ref("--short", HEAD, suppress=True, capture=True)
    stdout = git.stdout()
    if stdout:
        return stdout[-1]

    return None


@pyaud.plugins.register()
class Deploy(pyaud.plugins.Parametrize):
    """Deploy package documentation and test coverage."""

    def plugins(self) -> t.List[str]:
        return ["deploy-cov", "deploy-docs"]


@pyaud.plugins.register()
class DeployCov(pyaud.plugins.Action):
    """Upload coverage data to ``Codecov``.

    If no file exists otherwise announce that no file has been created
    yet.

    If no ``CODECOV_TOKEN`` environment variable has been exported or
    defined in ``.env`` announce that no authorization token has been
    created yet.
    """

    codecov = "codecov"

    @property
    def exe(self) -> t.List[str]:
        return [self.codecov]

    def action(self, *args: str, **kwargs: bool) -> int:
        self.logger().debug("looking for %s", e.COVERAGE_XML)
        if not e.COVERAGE_XML.is_file():
            print("No coverage report found")
            return 0

        if e.CODECOV_TOKEN is None:
            print("CODECOV_TOKEN not set")
            return 0

        return self.subprocess[self.codecov].call(
            "--file", e.COVERAGE_XML, **kwargs
        )


@pyaud.plugins.register()
class DeployDocs(pyaud.plugins.Action):  # pyli
    """Deploy package documentation to ``gh-pages``.

    Check that the branch is being pushed as master (or other branch for
    tests).

    If the correct branch is the one in use deploy. ``gh-pages`` to the
    orphaned branch - otherwise do nothing and announce.
    """

    _pushing_skipped = "Pushing skipped"
    _origin = "origin"
    _gh_pages = "gh-pages"

    def deploy_docs(self) -> None:
        """Series of functions for deploying docs."""
        root_html = Path.cwd() / "html"
        git.add(".")
        git.diff_index("--cached", HEAD, capture=True)
        stashed = False
        if git.stdout():
            git.stash(file=os.devnull)
            stashed = True

        shutil.move(str(e.DOCS_HTML), root_html)
        shutil.copy(e.README_RST, root_html / e.README_RST.name)
        git.rev_list("--max-parents=0", HEAD, capture=True)
        stdout = git.stdout()
        if stdout:
            git.checkout(stdout[-1])

        git.checkout("--orphan", self._gh_pages)
        git.config("--global", "user.name", e.GH_NAME)
        git.config("--global", "user.email", e.GH_EMAIL)
        shutil.rmtree(e.DOCS)
        git.rm("-rf", Path.cwd(), file=os.devnull)
        git.clean("-fdx", "--exclude=html", file=os.devnull)
        for file in root_html.rglob("*"):
            shutil.move(str(file), Path.cwd() / file.name)

        shutil.rmtree(root_html)
        git.add(".")
        git.commit(
            "-m",
            '"[ci skip] Publishes updated documentation"',
            file=os.devnull,
        )
        git.remote("rm", self._origin)
        git.remote("add", self._origin, e.GH_REMOTE)
        git.fetch()
        git.stdout()
        git.ls_remote("--heads", e.GH_REMOTE, self._gh_pages, capture=True)
        result = git.stdout()
        remote_exists = None if not result else result[-1]
        git.diff(
            self._gh_pages, "origin/gh-pages", suppress=True, capture=True
        )
        result = git.stdout()
        remote_diff = None if not result else result[-1]
        if remote_exists is not None and remote_diff is None:
            colors.green.print("No difference between local branch and remote")
            print(self._pushing_skipped)
        else:
            colors.green.print("Pushing updated documentation")
            git.push(self._origin, self._gh_pages, "-f")
            print("Documentation Successfully deployed")

        git.checkout("master", file=os.devnull)
        if stashed:
            git.stash("pop", file=os.devnull)

        git.branch("-D", self._gh_pages, file=os.devnull)

    def action(self, *args: str, **kwargs: bool) -> int:
        if branch() == "master":
            git_credentials = ["GH_NAME", "GH_EMAIL", "GH_TOKEN"]
            null_vals = [k for k in git_credentials if getattr(e, k) is None]
            if not null_vals:
                if not e.DOCS_HTML.is_dir():
                    pyaud.plugins.get("docs")(**kwargs)

                self.deploy_docs()
            else:
                print("The following is not set:")
                for null_val in null_vals:
                    print(f"- {e.PREFIX}{null_val}")

                print()
                print(self._pushing_skipped)
        else:
            colors.green.print("Documentation not for master")
            print(self._pushing_skipped)

        return 0


@pyaud.plugins.register()
class Readme(pyaud.plugins.Action):
    """Parse, test, and assert RST code-blocks."""

    readmetester = "readmetester"

    @property
    def env(self) -> t.Dict[str, str]:
        return {"PYCHARM_HOSTED": "True"}

    @property
    def exe(self) -> t.List[str]:
        return [self.readmetester]

    def action(self, *args: str, **kwargs: bool) -> int:
        return self.subprocess[self.readmetester].call(
            e.README_RST, *args, **kwargs
        )