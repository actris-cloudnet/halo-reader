from __future__ import annotations

import netCDF4
from attrs import define

from halo_reader.debug import *

from .attribute import Attribute


@define
class Metadata:
    filename: Attribute
    system_id: Attribute
    ngates: Attribute
    gate_range: Attribute
    gate_length: Attribute
    npulses: Attribute
    nrays: Attribute
    scantype: Attribute
    focus_range: Attribute
    start_time: Attribute
    resolution: Attribute

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        nc_meta = nc.createGroup("metadata")
        for attr_attr in self.__attrs_attrs__:
            metadata_attr = getattr(self, getattr(attr_attr, "name"))
            metadata_attr.nc_write(nc_meta)

    def __str__(self) -> str:
        str_ = ""
        for attr_attr in self.__attrs_attrs__:
            metadata_attr = getattr(self, getattr(attr_attr, "name"))
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
        for attr_attr in cls.__attrs_attrs__:
            name = getattr(attr_attr, "name")
            metadata_attr_list = [getattr(md, name) for md in metadata_list]
            metadata_attr_class = metadata_attr_list[0].__class__
            metadata_attr_merged = metadata_attr_class.merge(
                metadata_attr_list
            )
            metadata_attrs[name] = metadata_attr_merged
        return Metadata(**metadata_attrs)
