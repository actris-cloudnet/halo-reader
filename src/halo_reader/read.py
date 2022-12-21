import pkgutil
import re
from datetime import datetime, timezone
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import Any

import lark
import numpy as np
import numpy.typing as npt

from halo_reader.background_reader import read_background
from halo_reader.data_reader import read_data
from halo_reader.exceptions import BackgroundReadError
from halo_reader.halo import Halo, HaloBg
from halo_reader.metadata import Metadata
from halo_reader.type_guards import is_bytesio_list
from halo_reader.variable import Variable

from .exceptions import FileEmpty, HeaderNotFound
from .transformer import HeaderTransformer

grammar_header = pkgutil.get_data("halo_reader", "grammar_header.lark")
if not isinstance(grammar_header, bytes):
    raise FileNotFoundError("Header grammar file not found")
header_parser = lark.Lark(
    grammar_header.decode(), parser="lalr", transformer=HeaderTransformer()
)


def read(src: list[Path | BytesIO]) -> Halo | None:
    halos = []
    for i, s in enumerate(src):
        header_end, header_bytes = _read_header(s)
        metadata, time_vars, time_range_vars, range_func = header_parser.parse(
            header_bytes.decode()
        )
        data_bytes = _read_data(s, header_end)
        if not isinstance(metadata.ngates.data, int):
            raise TypeError
        read_data(data_bytes, metadata.ngates.data, time_vars, time_range_vars)
        vars = {var.name: var for var in time_vars + time_range_vars}
        vars["time"] = _decimaltime2timestamp(vars["time"], metadata)
        vars["range"] = range_func(vars["range"], metadata.gate_range)
        halos.append(Halo(metadata=metadata, **vars))
    return Halo.merge(halos)


def read_bg(
    src: list[Path | BytesIO], filenames: list[str] | None = None
) -> HaloBg | None:
    halobgs = []
    for s, fname in _bg_src_fname_list(src, filenames):
        bg_bytes = _read_background(s)
        background = read_background(bg_bytes)
        if not isinstance(background.data, np.ndarray):
            raise BackgroundReadError
        time = _bgfname2timevar(fname)
        range_ = Variable(
            name="range",
            units="index",
            dimensions=("range",),
            data=np.arange(background.data.shape[1]),
        )
        halobgs.append(HaloBg(time=time, background=background, range=range_))
    return HaloBg.merge(halobgs)


def _bgfname2timevar(fname: str) -> Variable:
    m = re.match(
        r"^Background_(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})\.txt$", fname
    )
    if m:
        dt = datetime(
            day=int(m.group(1)),
            month=int(m.group(2)),
            year=int("20" + m.group(3)),
            hour=int(m.group(4)),
            minute=int(m.group(5)),
            second=int(m.group(6)),
            tzinfo=timezone.utc,
        )
        return Variable(
            name="time",
            units="unix time",
            dimensions=("time",),
            data=np.array([dt.timestamp()]),
        )

    else:
        raise BackgroundReadError(
            f"Unexpected time format in filename: {fname}"
        )


def _bg_src_fname_list(
    src: list[Path | BytesIO], filenames: list[str] | None
) -> list[tuple[Path | BytesIO, str]]:
    src_fname_list: list[tuple[Path | BytesIO, str]] = []
    for i, s in enumerate(src):
        if isinstance(s, BytesIO):
            if filenames is None or len(filenames) != len(src):
                raise BackgroundReadError
            src_fname_list.append((s, filenames[i]))
        else:
            src_fname_list.append((s, s.name))
    return src_fname_list


def _decimaltime2timestamp(time: Variable, md: Metadata) -> Variable:
    if time.long_name != "decimal time" or time.units != "hours":
        raise NotImplementedError
    if md.start_time.units != "unix time":
        raise NotImplementedError
    day_in_seconds = 86400
    hour_in_seconds = 3600
    if (
        not isinstance(md.start_time.data, np.ndarray)
        or np.ndim(md.start_time.data) != 1
        or md.start_time.data.size != 1
    ):
        raise TypeError
    t_start = np.floor(md.start_time.data / day_in_seconds) * day_in_seconds
    if not isinstance(time.data, np.ndarray):
        raise TypeError
    time_ = t_start + hour_in_seconds * time.data
    i_day_changed = _find_change_of_day(0, time_)
    while i_day_changed >= 0:
        time_[i_day_changed:] += day_in_seconds
        i_day_changed = _find_change_of_day(i_day_changed, time_)
    return Variable(
        name="time", data=time_, dimensions=("time",), units="unix time"
    )


def _find_change_of_day(start: int, time: npt.NDArray) -> int:
    half_day = 43200
    for i, (a, b) in enumerate(zip(time[start:-1], time[start + 1 :])):
        if a - b > half_day:
            return i + 1
    return -1


def _read_header(src: Path | BytesIO) -> tuple[int, bytes]:
    if isinstance(src, Path):
        with src.open("rb") as src_buf:
            return _read_header_from_bytes(src_buf)
    else:
        return _read_header_from_bytes(src)


def _read_background(src: Path | BytesIO) -> bytes:
    if isinstance(src, Path):
        with src.open("rb") as src_buf:
            return src_buf.read()
    else:
        return src.read()


def _read_header_from_bytes(
    src: BufferedReader | BytesIO,
) -> tuple[int, bytes]:
    header_end = _find_header_end(src)
    if header_end < 0:
        src.seek(0)
        if len(src.read()) == 0:
            raise FileEmpty
        raise HeaderNotFound
    header_bytes = src.read(header_end)
    return header_end, header_bytes


def _read_data(src: Path | BytesIO, header_end: int) -> bytes:
    if isinstance(src, Path):
        with src.open("rb") as src_buf:
            src_buf.seek(header_end)
            return src_buf.read()
    else:
        src.seek(header_end)
        return src.read()


def _find_header_end(src: BufferedReader | BytesIO) -> int:
    guess = 1024
    loc_end = _try_header_end(src, guess)
    if loc_end < 0:
        loc_end = _try_header_end(src, 2 * guess)
    return loc_end


def _try_header_end(f: BufferedReader | BytesIO, guess: int) -> int:
    pos = f.tell()
    fbytes = f.read(guess)
    f.seek(pos)
    loc_sep = fbytes.find(b"****")
    if loc_sep < 0:
        return -1
    loc_end = fbytes.find(b"\r\n", loc_sep)
    if loc_end >= 0:
        loc_end += 2
    return loc_end
