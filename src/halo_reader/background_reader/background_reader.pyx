import numpy as np

from halo_reader.debug import *
from halo_reader.variable import Variable

from libc.stdlib cimport atof
from libc.string cimport strlen, strspn, strtok


def read_background(data_py: bytes) -> Variable:
    cdef char * data_c = data_py
    cdef char * token

    cdef unsigned long ntokens = 0
    token = strtok(data_c, " \r\n")
    while token != NULL:
        token = strtok(NULL, " \r\n")
        ntokens += 1

    data = np.zeros((1,ntokens), dtype=np.dtype("float"))
    cdef double [:,:] data_view = data

    cdef unsigned long i
    token = data_c
    for i in range(ntokens):
        data_view[0,i] = atof(token)
        token += strlen(token) + 1
        token += strspn(token, " \r\n")

    return Variable(
            name = "background",
            data = data,
            dimensions = ("time_background", "range_background")

            )
