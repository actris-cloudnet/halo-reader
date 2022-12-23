# HALO reader

[![Tests](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/halo-reader.svg)](https://badge.fury.io/py/halo-reader)

Reads and merges raw HALO Photonics wind doppler lidar files into a netCDF file.

Todo:

* [x] Support for different raw formats
* [x] Tests
* [ ] Standard/long netcdf variable names following CF Conventions

## Installation

```bash
# Requires python >= 3.10

# Install globally
python3 -m pip install halo-reader

# Or using virtual environment
python3 -m venv env
source env/bin/activate
pip install halo-reader
```

## Usage

```bash
halo2nc --help
halo2nc raw_file.hpl [another_raw_file.hpl ...] -o output.nc

# Background files
halobg2nc --help
halobg2nc Background_TIMESTAMP.txt [another_background_file.txt ...] -o output.nc
# TIMESTAMP format: ddmmyy-HHMMSS
```

## License

MIT
