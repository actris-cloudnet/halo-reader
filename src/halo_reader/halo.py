from __future__ import annotations

from dataclasses import dataclass

import netCDF4
import numpy.typing as npt

from halo_reader.debug import *
from halo_reader.metadata import Metadata
from halo_reader.variable import Variable


@dataclass(slots=True)
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
    spectral_width: Variable | None = None

    def __str__(self) -> str:
        str_ = ""
        for attr_name in self.__dataclass_fields__.keys():
            halo_field = getattr(self, attr_name)
            str_ += f"{halo_field}\n"
        return str_

    def __repr__(self) -> str:
        return str(self)

    def to_nc(self) -> memoryview:
        nc = netCDF4.Dataset("inmemory.nc", "w", memory=1028)
        self.time.nc_create_dimension(nc)
        self.range.nc_create_dimension(nc)
        for attr_name in self.__dataclass_fields__.keys():
            halo_attr = getattr(self, attr_name)
            if halo_attr is not None:
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
        for attr_name in cls.__dataclass_fields__.keys():
            halo_attr_list = [getattr(h, attr_name) for h in halos]
            halo_attr_class = halo_attr_list[0].__class__
            halo_attr_merged = halo_attr_class.merge(halo_attr_list)
            halo_attrs[attr_name] = halo_attr_merged
        return Halo(**halo_attrs)
