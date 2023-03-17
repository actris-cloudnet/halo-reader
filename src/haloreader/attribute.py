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

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        if isinstance(self.value, str):
            setattr(nc, self.name, self.value)
        elif isinstance(self.value, ScanType):
            setattr(nc, self.name, str(self.value))
        elif is_str_list(self.value):
            setattr(nc, self.name, "\n".join(self.value))

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
