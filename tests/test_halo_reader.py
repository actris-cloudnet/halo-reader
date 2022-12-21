import datetime
from pathlib import Path

import numpy as np
import pytest

from halo_reader.debug import *
from halo_reader.exceptions import FileEmpty, UnexpectedDataTokens
from halo_reader.read import read, read_bg

raw_files_pass = Path("tests/raw-files/pass/")
raw_files_xfail = Path("tests/raw-files/xfail/")


def test_eriswil():
    src = raw_files_pass.joinpath(
        "eriswil-2022-12-14-Stare_91_20221214_11.hpl"
    )
    halo = read([src])
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


def test_eriswil_merge():
    src_11 = raw_files_pass.joinpath(
        "eriswil-2022-12-14-Stare_91_20221214_11.hpl"
    )
    src_12 = raw_files_pass.joinpath(
        "eriswil-2022-12-14-Stare_91_20221214_12.hpl"
    )
    halo = read([src_11, src_12])
    time = datetime.datetime.utcfromtimestamp(halo.time.data[0]).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    assert time == "2022-12-14 11:00:17.979984"
    beta = halo.beta.data[0, 0]
    assert np.isclose(beta, 1.569249e-6)
    intensity = halo.intensity.data[0, 1]
    assert np.isclose(intensity, 1.014089)
    doppler_velocity = halo.doppler_velocity.data[-1, -1]
    assert np.isclose(doppler_velocity, -19.1484)
    halo.to_nc()


def test_soverato():
    src = raw_files_pass.joinpath(
        "soverato-2021-10-01-VAD_194_20210624_170110.hpl"
    )
    halo = read([src])
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
    halo = read([src])
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
        read([src])


def test_xfail_empty():
    src = raw_files_xfail.joinpath("empty.hpl")
    with pytest.raises(FileEmpty):
        read([src])


def test_eriswil_background():
    bg_dir = raw_files_pass.joinpath("eriswil-2022-12-14-background")
    bg_00 = bg_dir.joinpath("Background_141222-000013.txt")
    bg_01 = bg_dir.joinpath("Background_141222-010013.txt")
    halobg = read_bg([bg_00, bg_01])

    def timestr_fun(unix_time):
        return datetime.datetime.utcfromtimestamp(unix_time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    times = [timestr_fun(t) for t in halobg.time.data]
    assert times[0] == "2022-12-14 00:00:13"
    assert times[1] == "2022-12-14 01:00:13"
    bg = halobg.background
    assert bg.dimensions == ("time", "range")
    assert np.isclose(bg.data[0, 0], 610890.0)
    assert np.isclose(bg.data[0, 1], 14318556.375)
    assert np.isclose(bg.data[-1, -2], 16885681.125)
    assert np.isclose(bg.data[-1, -1], 16881329.375)
