# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.2.2] - 2025-01-25
### Changes
- Attempts to install the ``applescript`` Python package if not yet installed
  under macOS.


## [1.2.1] - 2025-01-22
### Changed
- Fix dependence on the `applescript` Python package.


## [1.2.0] - 2025-01-11
### Removed
- Support for Python 3.10.

### Added
- Column metadata formatting optional configuration.

### Changed
- Upgraded to [zensols.util] version 1.15.


## [1.1.2] - 2024-09-22
### Changed
- Bug fix when using Preview.app on macOS with files in names.
- Better handling of files with spaces in name.


## [1.1.1] - 2023-12-29
### Added
- Rendering of column metadata in [zensols.datdesc] `DataFrameDescriber`
  instance.


## [1.1.0] - 2023-12-05
### Changed
- Upgrade to [zensols.util] version 1.14.

### Added
- Support for Python 3.11.

### Removed
- Support for Python 3.9.


## [1.0.0] - 2023-11-16
Major feature release and project name change.

### Added
- Support for visualizing Excel, CSV, and TSV files using [Dash] `DataTable`s.

### Changed
- Application name from `showfile` to `rend` as the application now renders
  Pandas DataFrames.
- Renamed `Locator[Type]` to `Location[Type]` to standardize class naming.


## [0.3.0] - 2023-08-16
Downstream moderate risk update release.

### Changed
- Make Safari URL mangingling optional.
- Turn off Safari URL mangling by default.


## [0.2.0] - 2023-02-02
### Changed
- Updated [zensols.util] to 1.12.0.


## [0.1.0] - 2022-10-28
### Added
- Support for all operating systems for viewing files.


## [0.0.1] - 2022-08-24
### Added
- Initial version.


<!-- links -->
[Unreleased]: https://github.com/plandes/rend/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/plandes/rend/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/plandes/rend/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/plandes/rend/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/plandes/rend/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/plandes/rend/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/plandes/rend/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/plandes/rend/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/plandes/rend/compare/v0.1.1...v0.3.0
[0.2.0]: https://github.com/plandes/rend/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/plandes/rend/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/plandes/rend/compare/v0.0.0...v0.0.1

[Dash]: https://plotly.com/dash/
[zenbuild]: https://github.com/plandes/zenbuild
[zensols.datdesc]: https://github.com/plandes/datdesc
