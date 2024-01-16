<!--
This file is auto-generated and any changes made to it will be overwritten
-->
# tests

## tests._test

### tests._test.test_about_tests([tmp_path](#tests._test.test_about_tests.tmp_path): , [monkeypatch](#tests._test.test_about_tests.monkeypatch): , [main](#tests._test.test_about_tests.main): , [make_tree](#tests._test.test_about_tests.make_tree): , [capsys](#About tests.capsys): , [mock temporary directory]


Test test README is formatted correctly.

### tests._test.test_action([main](#tests._test.test_action.main): , [capsys](#tests._test.test_action.capsys): , [patch_sp_print_called](#tests._test.test_action.patch_sp_print_called): , [module](#Action.module): , [expected]


Test calling of `Action` plugin.

### tests._test.test_call_coverage_xml([main](#tests._test.test_call_coverage_xml.main): , [capsys](#tests._test.test_call_coverage_xml.capsys): , [patch_sp_print_called](#tests._test.test_call_coverage_xml.patch_sp_print_called): , [is_tests](#Call coverage xml.is tests): , [expected]


Test `coverage xml` is called after successful test run.

### tests._test.test_call_doctest_readme([monkeypatch](#tests._test.test_call_doctest_readme.monkeypatch): , [main](#Call doctest readme.main): , [capsys]


Test success and failure with `doctest-readme` plugin.

### tests._test.test_call_sort_pyproject([monkeypatch](#tests._test.test_call_sort_pyproject.monkeypatch): , [main](#Call sort pyproject.main): , [capsys]


Test register and call of `sort-pyproject` plugin.

### tests._test.test_change_logged_fail([monkeypatch](#tests._test.test_change_logged_fail.monkeypatch): , [main](#tests._test.test_change_logged_fail.main): , [commit_message](#Change logged fail.commit message): , [diff]


Test change-logged when failing.

### tests._test.test_change_logged_pass([monkeypatch](#tests._test.test_change_logged_pass.monkeypatch): , [main](#tests._test.test_change_logged_pass.main): , [commit_message](#Change logged pass.commit message): , [diff]


Test change-logged when passing.

### tests._test.test_commit_policy([monkeypatch](#tests._test.test_commit_policy.monkeypatch): , [main](#tests._test.test_commit_policy.main): , [make_tree](#Commit policy.make tree): , [capsys]


Test commit policy generation from .conform.yaml.

### tests._test.test_copyright_year([tmp_path](#tests._test.test_copyright_year.tmp_path): , [monkeypatch](#tests._test.test_copyright_year.monkeypatch): , [main](#tests._test.test_copyright_year.main): , [capsys](#tests._test.test_copyright_year.capsys): , [file](#tests._test.test_copyright_year.file): , [expected_year](#tests._test.test_copyright_year.expected_year): , [condition1](#tests._test.test_copyright_year.condition1): , [condition2](#tests._test.test_copyright_year.condition2): , [condition3](#tests._test.test_copyright_year.condition3): , [year](#Copyright year.year): , [\ copyright]


Test copyright year update for licenses.

### tests._test.test_docs([main](#tests._test.test_docs.main): , [monkeypatch](#tests._test.test_docs.monkeypatch): , [call_status](#Docs.call status): , [make tree]


Test `pyaud docs`.

### tests._test.test_doctest_readme([monkeypatch](#Doctest readme.monkeypatch), [main]


Test plugin for doctest.

### tests._test.test_download_missing_stubs([monkeypatch](#Download missing stubs.monkeypatch): , [main]


Test for coverage on missing stubs file.

### Get packages([make tree]


Test process when searching for project’s package.

### tests._test.test_nested_toc([monkeypatch](#tests._test.test_nested_toc.monkeypatch): , [main](#tests._test.test_nested_toc.main): , [capsys](#Nested toc.capsys): , [make tree]


Test that only one file is completed with a nested project.

Prior to this commit only `repo.src.rst` would be removed.

This commit will remove any file and copy its contents to the
single <NAME>.rst file e.g. `repo.routes.rst` is removed and
`repo.routes`, `repo.routes.auth`, `repo.routes.post`, and
`repo.routes.views` is added to repo.rst.

### tests._test.test_parametrize([main](#tests._test.test_parametrize.main): , [monkeypatch](#tests._test.test_parametrize.monkeypatch): , [capsys](#tests._test.test_parametrize.capsys): , [call_status](#tests._test.test_parametrize.call_status): , [module](#Parametrize.module): , [plugins]


Test the correct plugins are called when using `Parametrize`.

### Pycharm hosted([main]


Test that color codes are produced with `PYCHARM_HOSTED`.

### tests._test.test_pytest_is_tests([monkeypatch](#tests._test.test_pytest_is_tests.monkeypatch): , [main](#tests._test.test_pytest_is_tests.main): , [capsys](#tests._test.test_pytest_is_tests.capsys): , [patch_sp_print_called](#tests._test.test_pytest_is_tests.patch_sp_print_called): , [relpath](#Pytest is tests.relpath): , [expected]


Test that `pytest` is correctly called.

Test that `pytest` is not called if:

> - there is a test dir without tests
> - incorrect names within tests dir
> - no tests at all within tests dir.
### tests._test.test_readme_help([monkeypatch](#tests._test.test_readme_help.monkeypatch): , [main](#tests._test.test_readme_help.main): , [make_tree](#Readme help.make tree): , [capsys]


Test commit policy generation from .conform.yaml.

### tests._test.test_readme_help_no_commandline([monkeypatch](#tests._test.test_readme_help_no_commandline.monkeypatch): , [main](#Readme help no commandline.main): , [make tree]


Test commit policy generation from .conform.yaml.

### tests._test.test_readme_help_no_readme_rst([monkeypatch](#Readme help no readme rst.monkeypatch): , [main]


Test commit policy generation from .conform.yaml.

### Readme replace


Test that `LineSwitch` properly edits a file.

### tests._test.test_toc([tmp_path](#tests._test.test_toc.tmp_path): , [monkeypatch](#tests._test.test_toc.monkeypatch): , [main](#tests._test.test_toc.main): , [make_tree](#tests._test.test_toc.make_tree): , [patch_sp_call_null](#Toc.patch sp call null): , [capsys]


Test that the default toc file is edited correctly.

Ensure additional files generated by `sphinx-api` doc are removed.

### tests._test.test_typecheck_re_raise_err([monkeypatch](#Typecheck re raise err.monkeypatch): , [main]


Test for re-raise of error for non stub library errors.

### tests._test.test_whitelist([main](#tests._test.test_whitelist.main): , [monkeypatch](#Whitelist.monkeypatch): , [capsys]


Test a whitelist.py file is created properly.

Test for when piping data from `vulture --make-whitelist`.

