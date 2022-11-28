import pkgutil
from io import BufferedReader
from pathlib import Path

import lark
import numpy as np
import numpy.typing as npt

from halo_reader.data_reader import read_data
from halo_reader.halo import Halo
from halo_reader.variable import Variable
from halo_reader.metadata import Metadata
from .debug import *
from .exceptions import HeaderNotFound
from .transformer import HeaderTransformer

grammar_header = pkgutil.get_data("halo_reader", "grammar_header.lark")
if not isinstance(grammar_header, bytes):
    raise FileNotFoundError("Header grammar file not found")
header_parser = lark.Lark(
    grammar_header.decode(), parser="lalr", transformer=HeaderTransformer()
)


def read(src: list[Path], src_bg: list[Path]) -> None:
    for i, s in enumerate(src):
        header_end, header_bytes = _read_header(s)
        metadata, time_vars, time_range_vars, range_func = header_parser.parse(
            header_bytes.decode()
        )
        data_bytes = _read_data(s, header_end)
        read_data(data_bytes, metadata.ngates.value, time_vars, time_range_vars)
        vars = {var.name: var for var in time_vars + time_range_vars}
        vars["time"] = _decimaltime2timestamp(vars["time"], metadata)
        vars["range"] = range_func(vars["range"], metadata.gate_range)
        halo = Halo(metadata=metadata, **vars)
        print(halo)

def _decimaltime2timestamp(time: Variable, md: Metadata):
    if time.long_name != "decimal time" or time.units != "hours":
        raise NotImplementedError
    if md.start_time.units != "unix time":
        raise NotImplementedError
    t_start = np.floor(md.start_time.value)
    time_ = t_start + 3600*time.data
    #if _isdecreasing(time_):
    #    raise NotImplementedError
    return Variable(name="time", data=time_, dimensions=("time",), units="unix time" )

def _isdecreasing(x: npt.NDArray) -> bool:
    return np.any(np.diff(x) < 0)

def _read_header(src: Path) -> tuple[int, bytes]:
    with src.open("rb") as f:
        header_end = _find_header_end(f)
        if header_end < 0:
            raise HeaderNotFound
        header_bytes = f.read(header_end)
    return header_end, header_bytes

def _read_data(src: Path, header_end: int) -> bytes:
    with src.open("rb") as f:
        f.seek(header_end)
        return f.read()

def _find_header_end(f: BufferedReader) -> int:
    guess = 1024
    loc_end = _try_header_end(f, guess)
    if loc_end < 0:
        loc_end = _try_header_end(f, 2 * guess)
    return loc_end


def _try_header_end(f: BufferedReader, guess: int) -> int:
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
