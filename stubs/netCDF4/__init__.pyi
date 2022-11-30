import pathlib
from typing import Any, Literal

import numpy.typing as npt

FORMAT = Literal[
    "NETCDF4",
    "NETCDF4_CLASSIC",
    "NETCDF3_CLASSIC",
    "NETCDF3_64BIT_OFFSET",
    "NETCDF3_64BIT_DATA",
]
MODE = Literal["r", "w", "a", "r+", "rs", "ws", "as", "r+s"]

class Dataset:
    variables: dict
    dimensions: tuple[str, ...]
    data: npt.NDArray
    description: str
    units: str
    name: str

    def __init__(
        self,
        filename: str | pathlib.Path,
        mode: MODE = "r",
        clobber: bool = True,
        diskless: bool = False,
        persist: bool = False,
        keepweakref: bool = False,
        memory: bytes | int | None = None,
        encoding: str | None = None,
        parallel: bool = False,
        format: FORMAT = "NETCDF4",
    ): ...
    def createDimension(self, dimname: str, size: int | None) -> Dimension: ...
    def createVariable(
        self,
        varname: str,
        datatype: str,
        dimensions: tuple[str, ...] | None = None,
        compression: str | None = None,
        zlib: bool = False,
        complevel: int = 4,
        shuffle: bool = True,
        fletcher32: bool = False,
        contiguous: bool = False,
        chunksizes: tuple[int, ...] | None = None,
        szip_coding: str = "nn",
        szip_pixels_per_block: int = 8,
        blosc_shuffle: int = 1,
        endian: str = "native",
        least_significant_digit: int | None = None,
        significant_digits: int | None = None,
        quantize_mode: str = "BitGroom",
        fill_value: Any = None,
        chunk_cache: Any = None,
    ) -> Variable: ...
    def createGroup(self, groupname: str) -> Group: ...
    def ncattrs(self) -> list[str]: ...
    def __getitem__(self, *args: Any) -> Dataset: ...
    def __setitem__(self, *arg: Any) -> Dataset: ...
    def close(self) -> memoryview | None: ...

class Dimension: ...

class Variable:
    units: str
    standard_name: str
    long_name: str
    description: str
    def __getitem__(self, *args: Any) -> Variable: ...
    def __setitem__(self, *arg: Any) -> Variable: ...

class Group(Dataset): ...
