import numpy as np

from haloreader.variable import Variable

from libc.stdlib cimport atof
from libc.string cimport strlen, strspn, strtok


def read_background(data_py: bytes) -> Variable:
    if b"\n" not in data_py:
        return _read_background_without_newlines(data_py)
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
            dimensions = ("time", "range"),
            )


def _read_background_without_newlines(data_py: bytes) -> Variable:
    cdef char * data_c = data_py
    cdef char ch
    cdef char[32] num

    cdef unsigned long i = 0
    cdef unsigned long k = 0
    cdef unsigned long j = 0
    cdef unsigned long nchars = len(data_py)

    cdef unsigned long ntokens = 0
    while k < nchars:
        if data_c[k] == 46: # if '.'
            ntokens += 1
        k += 1

    data = np.zeros((1,ntokens), dtype=np.dtype("float"))
    cdef double [:,:] data_view = data

    k = 0
    while k < nchars:
        if data_c[k] == 46: # '.' is 46
            for _ in range(7):
                num[j] = data_c[k]
                k += 1
                j += 1
            num[j] = b"\0"
            data[0,i] = atof(num)
            i += 1
            j = 0
        else:
            num[j] = data_c[k]
            k += 1
            j += 1
    return Variable(
            name = "background",
            data = data,
            dimensions = ("time", "range"),
            )
