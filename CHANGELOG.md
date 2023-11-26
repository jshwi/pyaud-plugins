Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

[Unreleased](https://github.com/jshwi/pyaud-plugins/compare/v0.17.1...HEAD)
------------------------------------------------------------------------
### Security
- bump dependencies

[0.17.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.17.1) - 2023-09-09
------------------------------------------------------------------------
### Security
- bump pyaud

[0.17.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.17.0) - 2023-09-06
------------------------------------------------------------------------
### Changed
- remove `pyaud.Plugin.subprocess` for `subprocess.run`

[0.16.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.16.1) - 2023-08-12
------------------------------------------------------------------------
### Fixed
- ensure `pyaud readme-help` results are the same between versions

[0.16.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.16.0) - 2023-08-11
------------------------------------------------------------------------
### Added
- add `pyaud readme-help` plugin

[0.15.3](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.15.3) - 2023-08-04
------------------------------------------------------------------------
### Fixed
- only copy README.rst if it exists

[0.15.2](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.15.2) - 2023-08-04
------------------------------------------------------------------------
### Fixed
- build `pyaud about-tests` in temp dir

[0.15.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.15.1) - 2023-07-28
------------------------------------------------------------------------
### Fixed
- ensure no file leftover from `pyaud about-tests`

[0.15.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.15.0) - 2023-04-29
------------------------------------------------------------------------
### Changed
- Remove unused packages

### Fixed
- Remove `codecov` dependency

[0.14.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.14.0) - 2023-02-28
------------------------------------------------------------------------
### Added
- Add support for Python 3.10

[0.13.3](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.13.3) - 2023-02-26
------------------------------------------------------------------------
### Fixed
- Bump version constraints for `pyaud`

[0.13.2](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.13.2) - 2023-02-26
------------------------------------------------------------------------
### Fixed
- Fix version constraints for `pyaud`

[0.13.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.13.1) - 2023-02-20
------------------------------------------------------------------------
### Fixed
- Fix help for `pyaud imports`

[0.13.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.13.0) - 2023-02-20
------------------------------------------------------------------------
### Changed
- Update `Imports` to `CheckFix` subclass

[0.12.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.12.0) - 2023-02-05
------------------------------------------------------------------------
### Added
- Add `ChangeLogged` plugin

### Removed
- Remove `Requirements` plugin
- Remove deprecated plugins
- Remove logger for `DeployCov`

[0.11.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.11.0) - 2023-01-31
------------------------------------------------------------------------
### Added
- Add `CommitPolicy` plugin
- Add `AboutTests` plugin

[0.10.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.10.0) - 2023-01-04
------------------------------------------------------------------------
### Added
- Add py.typed

[0.9.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.9.0) - 2022-08-05
------------------------------------------------------------------------
### Security
- Removes Markdown parser which relies on `m2r` and `mistune`

[0.8.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.8.0) - 2022-08-04
------------------------------------------------------------------------
### Changed
- Removes reliability on `pyaud.environ` for env

[0.7.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.7.1) - 2022-06-29
------------------------------------------------------------------------
### Fixed
- Relaxes version constraints on some dependencies

[0.7.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.7.0) - 2022-06-24
------------------------------------------------------------------------
### Added
- Adds `params` plugin

[0.6.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.6.0) - 2022-05-04
------------------------------------------------------------------------
### Changed
- Migrates `pyaud_plugins._parsers` from `pyaud`

[0.5.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.5.0) - 2022-04-29
------------------------------------------------------------------------
### Added
- Adds individual file cache
- Adds cache to `pyaud doctest-package`

[0.4.2](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.4.2) - 2022-04-28
------------------------------------------------------------------------
### Fixed
Fixes `typecheck` plugin prior to v0.4.0

[0.4.1](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.4.1) - 2022-04-27
------------------------------------------------------------------------
### Fixed
- Fixes `format-docs` plugin prior to v0.4.0

[0.4.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.4.0) - 2022-04-26
------------------------------------------------------------------------
### Added
- Adds `test` plugin
- Adds `sort-pyproject` plugin
- Adds `doctest` plugin
- Adds `doctest-package` plugin
- Adds `doctest-readme` plugin
- Adds `const` plugin
- Adds more properties to `pyaud_plugins.environ`

### Changed
- `pyaud_plugins.environ` returns the absolute path

[0.3.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.3.0) - 2022-04-01
------------------------------------------------------------------------
### Changed
- Upgrades multiple plugin packages

[0.2.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.2.0) - 2022-01-09
------------------------------------------------------------------------
### Added
- Adds `pyaud_plugins.environ`

[0.1.0](https://github.com/jshwi/pyaud-plugins/releases/tag/v0.1.0) - 2022-01-09
------------------------------------------------------------------------
Initial Release
