# HALO reader

[![Tests](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/halo-reader.svg)](https://badge.fury.io/py/halo-reader)

**Package is under development and functionality/features might change.**

**Feedback is welcome:**
[mail](mailto:actris-cloudnet@fmi.fi) |
[create issue](https://github.com/actris-cloudnet/halo-reader/issues/new)

Reads and merges raw HALO Photonics wind doppler lidar files into a netCDF file.

Todo:

* [x] Support for different raw formats
* [x] Tests
* [ ] Standard/long netcdf variable names following CF Conventions

## Installation

```bash
# Requires python >= 3.10
git clone -b background-correction https://github.com/actris-cloudnet/halo-reader.git
cd halo-reader
# create a virtual environment
python3 -m venv env
# activate the virtual environment
source env/bin/activate
# install
pip install .
```

## Usage

```bash
# First activate the virtual environment, then
haloreader --help
haloreader from_raw --help
haloreader from_cloudnet --help
# Visualise
haloboard
# open your browser at localhost:5000
```

## License

MIT
