import logging
import pkgutil
import re
from datetime import datetime, timezone
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import Sequence

import lark
import numpy as np
import numpy.typing as npt
from lark.exceptions import UnexpectedInput

from haloreader.background_reader import read_background
from haloreader.data_reader import read_data
from haloreader.exceptions import BackgroundReadError
from haloreader.halo import Halo, HaloBg
from haloreader.metadata import Metadata
from haloreader.utils import UNIX_TIME_UNIT
from haloreader.variable import Variable

from .exceptions import (
    FileEmpty,
    HeaderNotFound,
    InconsistentRangeError,
    UnexpectedDataTokens,
)
from .transformer import HeaderTransformer

log = logging.getLogger(__name__)

grammar_header = pkgutil.get_data("haloreader", "grammar_header.lark")
if not isinstance(grammar_header, bytes):
    raise FileNotFoundError("Header grammar file not found")
header_parser = lark.Lark(
    grammar_header.decode(), parser="lalr", transformer=HeaderTransformer()
)


def _read_single(src: Path | BytesIO) -> Halo:
    header_end, header_bytes = _read_header(src)
    metadata, time_vars, time_range_vars, range_func = header_parser.parse(
        header_bytes.decode()
    )
    log.info("Reading data from %s", metadata.filename.value)
    data_bytes = _read_data(src, header_end)
    if not isinstance(metadata.ngates.data, int):
        raise TypeError
    read_data(data_bytes, metadata.ngates.data, time_vars, time_range_vars)
    vars_ = {var.name: var for var in time_vars + time_range_vars}
    if not _range_consistent(vars_["range"]):
        raise InconsistentRangeError
    vars_["time"] = _decimaltime2timestamp(vars_["time"], metadata)
    vars_["range"] = range_func(vars_["range"], metadata.gate_range)
    return Halo(metadata=metadata, **vars_)


def read(src_files: Sequence[Path | BytesIO]) -> Halo | None:
    halos = []
    for src in src_files:
        try:
            halos.append(_read_single(src))
        except (
            FileEmpty,
            HeaderNotFound,
            InconsistentRangeError,
            UnicodeDecodeError,
            UnexpectedInput,
            UnexpectedDataTokens,
        ) as err:
            log.warning("Skipping file", exc_info=err)
    log.info("Merging files")
    max_ngates = max(
        halo.metadata.ngates.data
        for halo in halos
        if isinstance(halo.metadata.ngates.data, int)
    )
    filtered_halos = [halo for halo in halos if halo.metadata.ngates.data == max_ngates]
    if len(halos) != len(filtered_halos):
        log.warning(
            "Skipping %s files with different number of gates",
            len(halos) - len(filtered_halos),
        )
    return Halo.merge(filtered_halos)


def _range_consistent(range_var: Variable) -> bool:
    if not isinstance(range_var.dimensions, tuple):
        raise TypeError
    if not isinstance(range_var.data, np.ndarray):
        raise TypeError
    if len(range_var.dimensions) != 2 or range_var.dimensions[1] != "range":
        return False
    expected_range = np.arange(range_var.data.shape[1], dtype=range_var.data.dtype)
    if all(np.allclose(expected_range, r) for r in range_var.data):
        return True
    return False


def read_bg(
    src_files: Sequence[Path | BytesIO], filenames: list[str] | None = None
) -> HaloBg | None:
    halobgs = []
    for src, fname in _bg_src_fname_list(src_files, filenames):
        bg_bytes = _read_background(src)
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
    if match_ := re.match(
        r"^Background_(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})\.txt$", fname
    ):
        return Variable(
            name="time",
            long_name="time of a background measurement",
            units=UNIX_TIME_UNIT,
            calendar="standard",
            dimensions=("time",),
            data=np.array(
                [
                    datetime(
                        day=int(match_.group(1)),
                        month=int(match_.group(2)),
                        year=int("20" + match_.group(3)),
                        hour=int(match_.group(4)),
                        minute=int(match_.group(5)),
                        second=int(match_.group(6)),
                        tzinfo=timezone.utc,
                    ).timestamp()
                ]
            ),
        )

    raise BackgroundReadError(f"Unexpected time format in filename: {fname}")


def _bg_src_fname_list(
    src_files: Sequence[Path | BytesIO], filenames: list[str] | None
) -> Sequence[tuple[Path | BytesIO, str]]:
    src_fname_list: list[tuple[Path | BytesIO, str]] = []
    for i, src in enumerate(src_files):
        if isinstance(src, BytesIO):
            if filenames is None or len(filenames) != len(src_files):
                raise BackgroundReadError
            src_fname_list.append((src, filenames[i]))
        else:
            src_fname_list.append((src, src.name))
    return src_fname_list


def _decimaltime2timestamp(time: Variable, metadata: Metadata) -> Variable:
    if time.long_name != "decimal time" or time.units != "hours":
        raise NotImplementedError
    if metadata.start_time.units != UNIX_TIME_UNIT:
        raise NotImplementedError
    day_in_seconds = 86400
    hour_in_seconds = 3600
    if (
        not isinstance(metadata.start_time.data, np.ndarray)
        or np.ndim(metadata.start_time.data) != 1
        or metadata.start_time.data.size != 1
    ):
        raise TypeError
    t_start = np.floor(metadata.start_time.data / day_in_seconds) * day_in_seconds
    if not isinstance(time.data, np.ndarray):
        raise TypeError
    time_ = t_start + hour_in_seconds * time.data
    i_day_changed = _find_change_of_day(0, time_)
    while i_day_changed >= 0:
        time_[i_day_changed:] += day_in_seconds
        i_day_changed = _find_change_of_day(i_day_changed, time_)
    return Variable(
        name="time",
        long_name="time",
        calendar="standard",
        data=time_,
        dimensions=("time",),
        units=UNIX_TIME_UNIT,
    )


def _find_change_of_day(start: int, time: npt.NDArray) -> int:
    half_day = 43200
    for i, (time_current, time_next) in enumerate(
        zip(time[start:-1], time[start + 1 :])
    ):
        if time_current - time_next > half_day:
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


def _try_header_end(file_io: BufferedReader | BytesIO, guess: int) -> int:
    pos = file_io.tell()
    fbytes = file_io.read(guess)
    file_io.seek(pos)
    loc_sep = fbytes.find(b"****")
    if loc_sep < 0:
        return -1
    loc_end = fbytes.find(b"\r\n", loc_sep)
    if loc_end >= 0:
        loc_end += 2
    return loc_end
