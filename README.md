# HALO reader – tool for HALO Photonics wind doppler lidar post-processing

[![Tests](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/actris-cloudnet/halo-reader/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/halo-reader.svg)](https://badge.fury.io/py/halo-reader)

**Package is under development and functionality/features might change.**

**Feedback is welcome:**
[mail](mailto:actris-cloudnet@fmi.fi) |
[create issue](https://github.com/actris-cloudnet/halo-reader/issues/new)


## Features

* Read and merge raw files into a netCDF file
* Read raw data directly from [Cloudnet](https://cloudnet.fmi.fi/) into a netCDF
* Visualise data


## Installation

```bash
# Requires Python 3.10 or newer

# create a virtual environment (optional)
python3 -m venv env
# activate the virtual environment
source env/bin/activate
# update pip
pip install -U pip

# install
pip install halo-reader
```

### Notes for Windows Subsystem for Linux (WSL) users

You can get Python 3.10 by installing [Ubuntu 22.04 from microsoft store](https://apps.microsoft.com/store/detail/ubuntu-22042-lts/9PN20MSR04DW).
In WSL, you may need to install `build-essential` and `python3-dev` before installing `halo-reader`.


## Usage

```bash
haloreader --help
haloreader from_raw --help
haloreader from_cloudnet --help
```

### Use data from cloudnet

```bash
# generate halo_warsaw_2023-03-16.nc file
# and vis/halo_warsaw_2023-13-16.png visualisation
haloreader from_cloudnet --site warsaw --date 2023-03-16 --plot

# Browse generated visualisations at /vis directory
haloboard
# open your browser at localhost:5000
```

### Use raw files

```bash
haloreader from_raw Stare_213_20230326_*.hpl Background_*0323-*.txt -o out.nc --plot

# Browse generated visualisations at /vis directory
haloboard
# open your browser at localhost:5000
```
**Note that a good background correction requires around 300 or more background profiles.**

## License

MIT
