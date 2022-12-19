# HALO reader

[![Tests](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml)

Reads raw HALO Photonics wind doppler lidar files into a netCDF file.

This python package is still in an alpha phase.

Todo:

* [x] Support for different raw formats
* [x] Tests
* [ ] Standard/long netcdf variable names following CF Conventions


## Installation

```bash
git clone git@github.com:actris-cloudnet/halo-reader.git
cd halo-reader

# Optional: Skip these two lines if you want to install globally
python3 -m venv env
source env/bin/activate

pip install .
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
