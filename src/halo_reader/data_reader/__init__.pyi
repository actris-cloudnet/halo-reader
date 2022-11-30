import cython

from halo_reader.variable import Variable

def read_data(
    data_py: bytes,
    ngates: cython.ulong,
    time_vars: list[Variable],
    time_range_vars: list[Variable],
) -> None: ...
