import cython

from halo_reader.variable import Variable

def read_background(
    data_py: bytes,
) -> Variable: ...
