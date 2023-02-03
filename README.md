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

# Install globally
python3 -m pip install halo-reader

# Or using virtual environment
python3 -m venv env
source env/bin/activate
pip install halo-reader
```

## Usage

### Convert raw files to netcdf

```bash
halo2nc --help
halo2nc raw_file.hpl [another_raw_file.hpl ...] -o output.nc

# Background files
halobg2nc --help
halobg2nc Background_TIMESTAMP.txt [another_background_file.txt ...] -o output.nc
# TIMESTAMP format: ddmmyy-HHMMSS
```

### Visualise raw files directly from Cloudnet

```python
from halodata.datasets import CloudnetData, CloudnetDataset
from haloboard.writer import Writer
import matplotlib.pyplot as plt

import logging
logging.basicConfig(level=logging.INFO)

dataset = CloudnetDataset(
    root="data",
    site="eriswil",
    scantype="stare",
    date_from="2023-01-01",
    date_to="2023-01-03",
)


writer = Writer()
for i, (date, halo, bg) in enumerate(dataset):
    fig, ax = plt.subplots(2,1, figsize=(18, 10))
    halo.plot(title=f"{date} intensity", ax = ax[0])
    bg.plot(title="background", ax = ax[1])
    writer.add_figure(f"halo-{date}", fig)
```
This downloads raw halo files into `data` folder,
and creates instensity and background plots into a `vis` folder.

Browse visualisations at `http://127.0.0.1:5000/`
```bash
haloboard
```





## License

MIT
