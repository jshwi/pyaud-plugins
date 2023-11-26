pyaud-plugins
=============
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: License
.. image:: https://img.shields.io/pypi/v/pyaud-plugins
    :target: https://pypi.org/project/pyaud-plugins/
    :alt: PyPI
.. image:: https://github.com/jshwi/pyaud-plugins/actions/workflows/build.yaml/badge.svg
    :target: https://github.com/jshwi/pyaud-plugins/actions/workflows/build.yaml
    :alt: Build
.. image:: https://github.com/jshwi/pyaud-plugins/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/jshwi/pyaud-plugins/actions/workflows/codeql-analysis.yml
    :alt: CodeQL
.. image:: https://results.pre-commit.ci/badge/github/jshwi/pyaud-plugins/master.svg
   :target: https://results.pre-commit.ci/latest/github/jshwi/pyaud-plugins/master
   :alt: pre-commit.ci status
.. image:: https://codecov.io/gh/jshwi/pyaud-plugins/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jshwi/pyaud-plugins
    :alt: codecov.io
.. image:: https://readthedocs.org/projects/pyaud-plugins/badge/?version=latest
    :target: https://pyaud-plugins.readthedocs.io/en/latest/?badge=latest
    :alt: readthedocs.org
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Black
.. image:: https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
    :target: https://pycqa.github.io/isort/
    :alt: isort
.. image:: https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg
    :target: https://github.com/PyCQA/docformatter
    :alt: docformatter
.. image:: https://img.shields.io/badge/linting-pylint-yellowgreen
    :target: https://github.com/PyCQA/pylint
    :alt: pylint
.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status
.. image:: https://snyk.io/test/github/jshwi/pyaud-plugins/badge.svg
    :target: https://snyk.io/test/github/jshwi/pyaud-plugins/badge.svg
    :alt: Known Vulnerabilities
.. image:: https://snyk.io/advisor/python/pyaud-plugins/badge.svg
    :target: https://snyk.io/advisor/python/pyaud-plugins
    :alt: pyaud-plugins

Plugin package for Pyaud
------------------------

Dependencies
------------

``pip install pyaud``

Install
-------

``pip install pyaud-plugins``

Development
-----------

``poetry install``

Usage
-----

See `pyaud <https://github.com/jshwi/pyaud#pyaud>`_

Plugins
-------

``pyaud`` will automatically load this package on search for all packages prefixed with `"pyaud_"`

For writing plugins see `docs <https://jshwi.github.io/pyaud/pyaud.html#pyaud-plugins>`_

This package contains the following plugins on running `pyaud modules`

.. code-block:: console

    about-tests     -- Check tests README is up-to-date
    audit           -- Read from [audit] key in config
    change-logged   -- Check commits with loggable tags are added to CHANGELOG
    commit-policy   -- Test commit policy is up to date
    const           -- Check code for repeat use of strings
    coverage        -- Run package unit-tests with `pytest` and `coverage`
    docs            -- Compile package documentation with `Sphinx`
    doctest         -- Run `doctest` on all code examples
    doctest-package -- Run `doctest` on package
    doctest-readme  -- Run `doctest` on Python code-blocks in README
    files           -- Audit project data files
    format          -- Audit code with `Black`
    format-docs     -- Format docstrings with `docformatter`
    format-str      -- Format f-strings with `flynt`
    imports         -- Audit imports with `isort`
    lint            -- Lint code with `pylint`
    modules         -- Display all available plugins and their documentation
    params          -- Check docstring params match function signatures
    readme-help     -- Test help documented in README is up to date
    sort-pyproject  -- Sort pyproject.toml file with `toml-sort`
    test            -- Run all tests
    tests           -- Run the package unit-tests with `pytest`
    toc             -- Audit docs/<NAME>.rst toc-file
    typecheck       -- Typecheck code with `mypy`
    unused          -- Audit unused code with `vulture`
    whitelist       -- Check whitelist.py file with `vulture`
