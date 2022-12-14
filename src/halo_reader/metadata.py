from __future__ import annotations

from dataclasses import dataclass

import netCDF4

from halo_reader.debug import *

from .attribute import Attribute


@dataclass(slots=True)
class Metadata:
    filename: Attribute
    system_id: Attribute
    ngates: Attribute
    gate_range: Attribute
    gate_length: Attribute
    npulses: Attribute
    scantype: Attribute
    focus_range: Attribute
    start_time: Attribute
    resolution: Attribute
    nrays: Attribute | None = None
    nwaypoints: Attribute | None = None

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        nc_meta = nc.createGroup("metadata")
        for attr_name in self.__dataclass_fields__.keys():
            metadata_attr = getattr(self, attr_name)
            if metadata_attr is not None:
                metadata_attr.nc_write(nc_meta)

    def __str__(self) -> str:
        str_ = ""
        for attr_name in self.__dataclass_fields__.keys():
            metadata_attr = getattr(self, attr_name)
            str_ += f"{metadata_attr}\n"
        return str_

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def merge(cls, metadata_list: list[Metadata]) -> Metadata | None:
        if len(metadata_list) == 0:
            return None
        if len(metadata_list) == 1:
            return metadata_list[0]
        metadata_attrs = {}
        for attr_name in cls.__dataclass_fields__.keys():
            metadata_attr_list = [
                getattr(md, attr_name) for md in metadata_list
            ]
            metadata_attr_class = metadata_attr_list[0].__class__
            metadata_attr_merged = metadata_attr_class.merge(
                metadata_attr_list
            )
            metadata_attrs[attr_name] = metadata_attr_merged
        return Metadata(**metadata_attrs)
