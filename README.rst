pyaud-plugins
=============
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: License
.. image:: https://img.shields.io/pypi/v/pyaud-plugins
    :target: https://img.shields.io/pypi/v/pyaud-plugins
    :alt: pypi
.. image:: https://github.com/jshwi/pyaud-plugins/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/jshwi/pyaud-plugins/actions/workflows/ci.yml
    :alt: CI
.. image:: https://github.com/jshwi/pyaud-plugins/actions/workflows/codeql-analysis.yml/badge.svg
    :target: https://github.com/jshwi/pyaud-plugins/actions/workflows/codeql-analysis.yml
    :alt: CodeQL
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
    :alt: black

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

    const           -- Check code for repeat use of strings
    coverage        -- Run package unit-tests with `pytest` and `coverage`
    deploy          -- Deploy package documentation and test coverage
    deploy-cov      -- Upload coverage data to `Codecov`
    deploy-docs     -- Deploy package documentation to `gh-pages`
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
    readme          -- Parse, test, and assert RST code-blocks
    requirements    -- Audit requirements.txt with Pipfile.lock
    sort-pyproject  -- Sort pyproject.toml file with `toml-sort`
    test            -- Run all tests
    tests           -- Run the package unit-tests with `pytest`
    toc             -- Audit docs/<NAME>.rst toc-file
    typecheck       -- Typecheck code with `mypy`
    unused          -- Audit unused code with `vulture`
    whitelist       -- Check whitelist.py file with `vulture`
