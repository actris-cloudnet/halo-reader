# Changelog

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

## [0.1.5] - 2023-09-22

### Changed
- Skip files with different number of gates

## [0.1.4] - 2023-09-15

### Fixed
- Handle background file with zeros
- Support background file without newlines

## [0.1.3] - 2023-09-14

### Fixed
- Allow missing pitch and roll

## [0.1.2] - 2023-04-28

### Added
- Raise error if range gate indexing is inconsitent
- Add plotting for beta and screened variables

### Changed
- Screen values where intensity is below one

## [0.1.1] - 2023-04-25

### Changed
- Skip invalid input files in `read` function

## [0.1.0] - 2023-04-20

### Changed
- Ignore profiles where timestamps are not increasing

### Fixed

## [0.0.9] - 2023-04-13

### Changed
- default wavelength from 1.5um to 1.565um

## [0.0.8] - 2023-04-12

### Added
- Add posibility to change variable and attribute names in netCDF
- Exclude variables from netCDF
- Add screened beta and doppler velocity

## [0.0.7] - 2023-04-03

### Added
- Add nu and eta for beta (still for testing)

## [0.0.6] - 2023-03-31

### Added
- Compute beta using placeholder values (for testing)

### Changed
- Use float instead of douple in data arrays (excluding time)

## [0.0.5] - 2023-03-30

### Fixed
- Fix installation instructions

## [0.0.4] - 2023-03-29

### Fixed
- Fix missing style file

## [0.0.3] - 2023-03-28

### Added
- Added `halodata` package to iterate over halo doppler lidar data from Cloudnet
- Added `haloboard` package for data visualisations
- Added tests for CF Convention compliance

[0.0.3]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.3
[0.0.4]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.4
[0.0.5]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.5
[0.0.6]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.6
[0.0.7]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.7
[0.0.8]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.8
[0.0.9]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.0.9
[0.1.0]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.0
[0.1.1]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.1
[0.1.2]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.2
[0.1.3]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.3
[0.1.4]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.4
[0.1.5]: https://github.com/actris-cloudnet/halo-reader/releases/tag/v0.1.5
