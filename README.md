# HALO reader - tool for HALO Photonics wind doppler lidar post-processing

[![Tests](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/halo-reader.svg)](https://badge.fury.io/py/halo-reader)

**Package is under development and functionality/features might change.**

**Feedback is welcome:**
[mail](mailto:actris-cloudnet@fmi.fi) |
[create issue](https://github.com/actris-cloudnet/halo-reader/issues/new)


## Features:
* Read and merge raw files into a netCDF file.
* Reads raw data directly from [Cloudnet](https://cloudnet.fmi.fi/) into a netCDF
* visualisations


Todo:

* [ ] Standard/long netcdf variable names following CF Conventions

## Installation

```bash
# Requires python >= 3.10
git clone https://github.com/actris-cloudnet/halo-reader.git
cd halo-reader
# create a virtual environment
python3 -m venv env
# activate the virtual environment
source env/bin/activate
# install
pip install .
```

### Notes for Windows Subsystem for Linux (WSL) users
You can get python3.10 >= by installing [Ubuntu 22.04 from microsoft store](https://apps.microsoft.com/store/detail/ubuntu-22042-lts/9PN20MSR04DW).
In WSL, you may need to install `build-essential` and `python3.10-dev` before installing `halo-reader`.


## Usage

### Use data from cloudnet
```bash
# generate halo_warsaw_2023-03-16.nc file
# and vis/halo_warsaw_2023-13-16.png visualisation
haloreader from_cloudnet --site warsaw --date 2023-03-16 --plot

# Browse generated visualisations at /vis directory
haloboard
# open your browser at localhost:5000
```

## License

MIT
