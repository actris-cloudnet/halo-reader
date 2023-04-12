from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeGuard

import netCDF4

from haloreader.scantype import ScanType
from haloreader.type_guards import is_str_list


@dataclass(slots=True)
class Attribute:
    name: str
    value: str | ScanType | list[str]

    def nc_write(
        self,
        nc: netCDF4.Dataset,
        nc_map: dict[str, dict] | None = None,
        nc_exclude: dict[str, set] | None = None,
    ) -> None:
        nc_exclude_attr = (
            nc_exclude.get("attributes", set()) if nc_exclude is not None else set()
        )
        if self.name in nc_exclude_attr:
            return
        nc_map_attr = nc_map.get("attributes", {}) if nc_map is not None else {}
        name = nc_map_attr.get(self.name, self.name)
        if isinstance(self.value, str):
            setattr(nc, name, self.value)
        elif isinstance(self.value, ScanType):
            setattr(nc, name, str(self.value))
        elif is_str_list(self.value):
            setattr(nc, name, "\n".join(self.value))

    @classmethod
    def is_attribute_list(cls, val: list[Any]) -> TypeGuard[list[Attribute]]:
        return all(isinstance(x, Attribute) for x in val)

    @classmethod
    def merge(cls, attributes: list[Attribute]) -> Attribute | None:
        if len(attributes) == 0:
            return None
        if len(attributes) == 1:
            return attributes[0]

        first_attr = attributes[0]
        names_eq = all(first_attr.name == a.name for a in attributes[1:])
        values_eq = all(first_attr.value == a.value for a in attributes[1:])

        if names_eq and values_eq:
            return attributes[0]
        if names_eq and first_attr.name == "filename":
            return Attribute(name=first_attr.name, value=_list_values(attributes))
        raise ValueError(f"Cannot merge attribute {attributes[0].name}")


def _list_values(attributes: list[Attribute]) -> list[str]:
    value_list = [a.value for a in attributes]
    if is_str_list(value_list):
        return value_list
    raise TypeError


def _str_or_str_list2str(val: str | list[str]) -> str:
    if isinstance(val, list):
        return "\n".join(val)
    return val
