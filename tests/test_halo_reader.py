import datetime
from pathlib import Path

import numpy as np
import pytest

from halo_reader.debug import *
from halo_reader.exceptions import FileEmpty, UnexpectedDataTokens
from halo_reader.read import read

raw_files_pass = Path("tests/raw-files/pass/")
raw_files_xfail = Path("tests/raw-files/xfail/")


def test_eriswil():
    src = raw_files_pass.joinpath(
        "eriswil-2022-12-14-Stare_91_20221214_11.hpl"
    )
    halo = read([src], src_bg=[])
    time = datetime.datetime.utcfromtimestamp(halo.time.data[0]).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    assert time == "2022-12-14 11:00:17.979984"
    beta = halo.beta.data[0, 0]
    assert np.isclose(beta, 1.569249e-6)
    intensity = halo.intensity.data[0, 1]
    assert np.isclose(intensity, 1.014089)
    doppler_velocity = halo.doppler_velocity.data[-1, -1]
    assert np.isclose(doppler_velocity, 16.1290)
    halo.to_nc()


def test_soverato():
    src = raw_files_pass.joinpath(
        "soverato-2021-10-01-VAD_194_20210624_170110.hpl"
    )
    halo = read([src], src_bg=[])
    assert halo.time.data.shape == (2,)
    assert halo.azimuth.data.shape == (2,)
    assert halo.elevation.data.shape == (2,)
    assert halo.pitch.data.shape == (2,)
    assert halo.roll.data.shape == (2,)
    assert halo.intensity.data.shape == (2, 400)
    assert halo.beta.data.shape == (2, 400)
    assert halo.doppler_velocity.data.shape == (2, 400)
    halo.to_nc()


def test_warsaw():
    src = raw_files_pass.joinpath(
        "warsaw-2022-12-13-Stare_213_20221213_04.hpl"
    )
    halo = read([src], src_bg=[])
    assert halo.time.data.shape == (2,)
    assert halo.azimuth.data.shape == (2,)
    assert halo.elevation.data.shape == (2,)
    assert halo.pitch.data.shape == (2,)
    assert halo.roll.data.shape == (2,)
    assert halo.intensity.data.shape == (2, 333)
    assert halo.beta.data.shape == (2, 333)
    assert halo.doppler_velocity.data.shape == (2, 333)
    halo.to_nc()


def test_xfail_warsaw():
    src = raw_files_xfail.joinpath(
        "warsaw-2021-10-01-Stare_213_20211001_18.hpl"
    )
    with pytest.raises(UnexpectedDataTokens):
        read([src], src_bg=[])


def test_xfail_empty():
    src = raw_files_xfail.joinpath("empty.hpl")
    with pytest.raises(FileEmpty):
        read([src], src_bg=[])
