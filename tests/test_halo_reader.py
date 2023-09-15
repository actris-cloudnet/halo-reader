import datetime
import tempfile
from pathlib import Path

import numpy as np
import pytest
from cfchecker import cfchecks

from haloreader.exceptions import FileEmpty, UnexpectedDataTokens
from haloreader.read import _read_single, read

raw_files_pass = Path("tests/raw-files/pass/")
raw_files_xfail = Path("tests/raw-files/xfail/")


def _check_cf_conventions(nc_buf):
    f = tempfile.NamedTemporaryFile(suffix=".nc")
    f.write(nc_buf)
    cf_instance = cfchecks.CFChecker()
    res = cf_instance.checker(f.name)
    err = [val["ERROR"] for val in res["variables"].values() if len(val["ERROR"]) > 0]
    assert len(err) == 0, str(res)


def test_eriswil():
    src = raw_files_pass.joinpath("eriswil-2022-12-14-Stare_91_20221214_11.hpl")
    halo = read([src])
    time = datetime.datetime.utcfromtimestamp(halo.time.data[0]).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    assert time == "2022-12-14 11:00:17.979984"
    beta_raw = halo.beta_raw.data[0, 0]
    assert np.isclose(beta_raw, 1.569249e-6)
    intensity = halo.intensity_raw.data[0, 1]
    assert np.isclose(intensity, 1.014089)
    doppler_velocity = halo.doppler_velocity.data[-1, -1]
    assert np.isclose(doppler_velocity, 16.1290)
    buf = halo.to_nc()
    _check_cf_conventions(buf)


def test_eriswil_merge():
    src_11 = raw_files_pass.joinpath("eriswil-2022-12-14-Stare_91_20221214_11.hpl")
    src_12 = raw_files_pass.joinpath("eriswil-2022-12-14-Stare_91_20221214_12.hpl")
    halo = read([src_11, src_12])
    time = datetime.datetime.utcfromtimestamp(halo.time.data[0]).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )
    assert time == "2022-12-14 11:00:17.979984"
    beta_raw = halo.beta_raw.data[0, 0]
    assert np.isclose(beta_raw, 1.569249e-6)
    intensity = halo.intensity_raw.data[0, 1]
    assert np.isclose(intensity, 1.014089)
    doppler_velocity = halo.doppler_velocity.data[-1, -1]
    assert np.isclose(doppler_velocity, -19.1484)
    buf = halo.to_nc()
    _check_cf_conventions(buf)


def test_soverato():
    src = raw_files_pass.joinpath("soverato-2021-10-01-VAD_194_20210624_170110.hpl")
    halo = read([src])
    assert halo.time.data.shape == (2,)
    assert halo.azimuth.data.shape == (2,)
    assert halo.elevation.data.shape == (2,)
    assert halo.pitch.data.shape == (2,)
    assert halo.roll.data.shape == (2,)
    assert halo.intensity_raw.data.shape == (2, 400)
    assert halo.beta_raw.data.shape == (2, 400)
    assert halo.doppler_velocity.data.shape == (2, 400)
    buf = halo.to_nc()
    _check_cf_conventions(buf)


def test_warsaw():
    src = raw_files_pass.joinpath("warsaw-2022-12-13-Stare_213_20221213_04.hpl")
    halo = read([src])
    assert halo.time.data.shape == (2,)
    assert halo.azimuth.data.shape == (2,)
    assert halo.elevation.data.shape == (2,)
    assert halo.pitch.data.shape == (2,)
    assert halo.roll.data.shape == (2,)
    assert halo.intensity_raw.data.shape == (2, 333)
    assert halo.beta_raw.data.shape == (2, 333)
    assert halo.doppler_velocity.data.shape == (2, 333)
    buf = halo.to_nc()
    _check_cf_conventions(buf)


def test_hyytiala():
    src = raw_files_pass.joinpath("hyytiala-2023-09-13-Stare_46_20230913_23.hpl")
    halo = read([src])
    assert halo.time.data.shape == (1,)
    assert halo.azimuth.data.shape == (1,)
    assert halo.elevation.data.shape == (1,)
    assert halo.pitch is None
    assert halo.roll is None
    assert halo.intensity_raw.data.shape == (1, 320)
    assert halo.beta_raw.data.shape == (1, 320)
    assert halo.doppler_velocity.data.shape == (1, 320)
    buf = halo.to_nc()
    _check_cf_conventions(buf)


def test_xfail_warsaw():
    src = raw_files_xfail.joinpath("warsaw-2021-10-01-Stare_213_20211001_18.hpl")
    with pytest.raises(UnexpectedDataTokens):
        _read_single(src)


def test_xfail_empty():
    src = raw_files_xfail.joinpath("empty.hpl")
    with pytest.raises(FileEmpty):
        _read_single(src)
