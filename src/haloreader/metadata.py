from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeGuard

import netCDF4

from haloreader.type_guards import is_none_list
from haloreader.version import __version__ as pkgversion

from .attribute import Attribute
from .variable import Variable


@dataclass(slots=True)
class Metadata:
    filename: Attribute
    system_id: Attribute
    ngates: Variable
    gate_range: Variable
    gate_length: Variable
    npulses: Variable
    scantype: Attribute
    focus_range: Variable
    start_time: Variable
    resolution: Variable
    nrays: Variable | None = None
    nwaypoints: Variable | None = None
    instrument_spectral_width: Variable | None = None
    haloreader_version: Attribute = field(
        default_factory=lambda: Attribute(name="haloreader_version", value=pkgversion)
    )
    conventions: Attribute = field(
        default_factory=lambda: Attribute(name="Conventions", value="CF-1.8")
    )

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        # nc_meta = nc.createGroup("metadata")
        nc_meta = nc
        for attr_name in self.__dataclass_fields__.keys():
            metadata_attr = getattr(self, attr_name)
            if metadata_attr is not None:
                metadata_attr.nc_write(nc_meta)

    @classmethod
    def merge(cls, metadata_list: list[Metadata]) -> Metadata | None:
        if len(metadata_list) == 0:
            return None
        if len(metadata_list) == 1:
            return metadata_list[0]
        metadata_attrs: dict[str, Any] = {}
        for attr_name in cls.__dataclass_fields__.keys():
            metadata_attr_list = [getattr(md, attr_name) for md in metadata_list]

            if Attribute.is_attribute_list(metadata_attr_list):
                metadata_attrs[attr_name] = Attribute.merge(metadata_attr_list)
            elif Variable.is_variable_list(metadata_attr_list):
                metadata_attrs[attr_name] = Variable.merge(metadata_attr_list)
            elif is_none_list(metadata_attr_list):
                metadata_attrs[attr_name] = None
            else:
                raise TypeError
        return Metadata(**metadata_attrs)

    @classmethod
    def is_metadata_list(cls, val: list[Any]) -> TypeGuard[list[Metadata]]:
        return all(isinstance(x, Metadata) for x in val)
