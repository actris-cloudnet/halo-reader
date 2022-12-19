import numpy as np

from halo_reader.exceptions import UnexpectedDataTokens
from halo_reader.variable import Variable

from libc.stdlib cimport atof
from libc.string cimport strlen, strspn, strtok

import cython


def read_data(data_py: bytes, ngates: cython.ulong, time_vars: list[Variable], time_range_vars: list[Variable]) -> None:
    cdef char * data_c = data_py
    cdef char * token

    # Count tokens and nprofiles
    cdef unsigned long ntokens = 0
    token = strtok(data_c, " \r\n")
    while token != NULL:
        token = strtok(NULL, " \r\n")
        ntokens += 1
    cdef unsigned long ntime_vars = len(time_vars)
    cdef unsigned long ntime_range_vars = len(time_range_vars)
    cdef unsigned long nprofiles = ntokens // (ntime_vars + ngates * ntime_range_vars)
    if (ntime_vars + ngates * ntime_range_vars) * nprofiles != ntokens:
        # Some files might have extra time_range_var column for spectral width
        nprofiles = ntokens // (ntime_vars + ngates * (ntime_range_vars+1))
        if (ntime_vars + ngates * (ntime_range_vars+1)) * nprofiles == ntokens:
            ntime_range_vars += 1
            time_range_vars.append(Variable(name="spectral_width"))
        else:
            raise UnexpectedDataTokens


    data_time = np.zeros((nprofiles,ntime_vars), dtype=np.dtype("float"))
    data_time_range = np.zeros((nprofiles,ngates,ntime_range_vars), dtype=np.dtype("float"))
    cdef double [:,:] data_time_view = data_time
    cdef double [:,:,:] data_time_range_view = data_time_range



    cdef unsigned long p, tvar, g, trvar
    token = data_c
    for p in range(nprofiles):
        for tvar in range(ntime_vars):
            data_time_view[p,tvar] = atof(token)
            token += strlen(token) + 1
            token += strspn(token, " \r\n")
        for g in range(ngates):
            for trvar in range(ntime_range_vars):
                data_time_range_view[p,g,trvar] = atof(token)
                token += strlen(token) + 1
                token += strspn(token, " \r\n")

    for i,var in enumerate(time_vars):
        var.data = data_time[:,i]
        var.dimensions = ("time",)
    for i,var in enumerate(time_range_vars):
        var.data = data_time_range[:,:,i]
        var.dimensions = ("time","range")
