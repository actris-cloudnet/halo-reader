import datetime
from pathlib import Path

import numpy as np

from haloreader.read import read_bg

raw_files_pass = Path("tests/raw-files/pass/")


def timestr(unix_time):
    return datetime.datetime.utcfromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")


def test_eriswil_background():
    bg_dir = raw_files_pass.joinpath("eriswil-2022-12-14-background")
    bg_00 = bg_dir.joinpath("Background_141222-000013.txt")
    bg_01 = bg_dir.joinpath("Background_141222-010013.txt")
    halobg = read_bg([bg_00, bg_01])

    times = halobg.time.data
    assert timestr(times[0]) == "2022-12-14 00:00:13"
    assert timestr(times[1]) == "2022-12-14 01:00:13"
    bg = halobg.background
    assert bg.dimensions == ("time", "range")
    assert bg.data.shape == (2, 250)
    assert np.isclose(bg.data[0, 0], 610890.0)
    assert np.isclose(bg.data[0, 1], 14318556.375)
    assert np.isclose(bg.data[-1, -2], 16885681.125)
    assert np.isclose(bg.data[-1, -1], 16881329.375)


def test_hyytiala_background():
    bg_dir = raw_files_pass.joinpath("hyytiala-2023-08-15-background")
    bg_00 = bg_dir.joinpath("Background_150823-122811.txt")
    halobg = read_bg([bg_00])

    times = halobg.time.data
    assert timestr(times[0]) == "2023-08-15 12:28:11"
    bg = halobg.background
    assert bg.dimensions == ("time", "range")
    assert bg.data.shape == (1, 400)
    assert np.isclose(bg.data[0, 0], 575587.333333)
    assert np.isclose(bg.data[0, 1], 14902110.166667)
