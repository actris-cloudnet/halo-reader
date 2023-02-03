import cython

from haloreader.variable import Variable

def read_background(
    data_py: bytes,
) -> Variable: ...
