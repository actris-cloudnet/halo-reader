from __future__ import annotations

import netCDF4
import numpy.typing as npt
from attrs import define

from halo_reader.debug import *
from halo_reader.metadata import Metadata
from halo_reader.variable import Variable


@define
class Halo:
    metadata: Metadata
    time: Variable
    range: Variable
    azimuth: Variable
    elevation: Variable
    pitch: Variable
    roll: Variable
    doppler_velocity: Variable
    intensity: Variable
    beta: Variable

    def __str__(self) -> str:
        str_ = ""
        for attr_attr in self.__attrs_attrs__:
            halo_attr = getattr(self, getattr(attr_attr, "name"))
            str_ += f"{halo_attr}\n"
        return str_

    def __repr__(self) -> str:
        return str(self)

    def to_nc(self) -> memoryview:
        nc = netCDF4.Dataset("inmemory.nc", "w", memory=1028)
        self.time.nc_create_dimension(nc)
        self.range.nc_create_dimension(nc)
        for attr_attr in self.__attrs_attrs__:
            halo_attr = getattr(self, getattr(attr_attr, "name"))
            halo_attr.nc_write(nc)
        nc_buf = nc.close()
        if isinstance(nc_buf, memoryview):
            return nc_buf
        else:
            raise TypeError

    @classmethod
    def merge(cls, halos: list[Halo]) -> Halo | None:
        if len(halos) == 0:
            return None
        if len(halos) == 1:
            return halos[0]
        halo_attrs = {}
        for attr_attr in cls.__attrs_attrs__:
            name = getattr(attr_attr, "name")
            halo_attr_list = [getattr(h, name) for h in halos]
            halo_attr_class = halo_attr_list[0].__class__
            halo_attr_merged = halo_attr_class.merge(halo_attr_list)
            halo_attrs[name] = halo_attr_merged
        return Halo(**halo_attrs)
