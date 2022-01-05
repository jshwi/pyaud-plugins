pyaud-plugins
=============
.. image:: https://github.com/jshwi/pyaud-plugins/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/jshwi/pyaud-plugins/actions/workflows/ci.yml
    :alt: ci
.. image:: https://img.shields.io/badge/python-3.8-blue.svg
    :target: https://www.python.org/downloads/release/python-380
    :alt: python3.8
.. image:: https://img.shields.io/pypi/v/pyaud-plugins
    :target: https://img.shields.io/pypi/v/pyaud-plugins
    :alt: pypi
.. image:: https://codecov.io/gh/jshwi/pyaud-plugins/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/jshwi/pyaud-plugins
    :alt: codecov.io
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://lbesson.mit-license.org/
    :alt: mit
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: black

Plugins for `pyaud`

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

    coverage        -- Run package unit-tests with `pytest` and `coverage`
    deploy          -- Deploy package documentation and test coverage
    deploy-cov      -- Upload coverage data to `Codecov`
    deploy-docs     -- Deploy package documentation to `gh-pages`
    docs            -- Compile package documentation with `Sphinx`
    files           -- Audit project data files
    format          -- Audit code against `Black`
    format-docs     -- Format docstrings with `docformatter`
    format-str      -- Format f-strings with `flynt`
    imports         -- Audit imports with `isort`
    lint            -- Lint code with `pylint`
    readme          -- Parse, test, and assert RST code-blocks
    requirements    -- Audit requirements.txt with Pipfile.lock
    tests           -- Run the package unit-tests with `pytest`
    toc             -- Audit docs/<NAME>.rst toc-file
    typecheck       -- Typecheck code with `mypy`
    unused          -- Audit unused code with `vulture`
    whitelist       -- Check whitelist.py file with `vulture`
