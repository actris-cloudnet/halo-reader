from __future__ import annotations


from attrs import define
from halo_reader.utils import two_column_format
from halo_reader.utils import timestamp2str
from typing import TypeAlias

from halo_reader.debug import *
from halo_reader.scantype import ScanType
from halo_reader.type_guards import is_float_or_float_list
from halo_reader.type_guards import is_float_list
from halo_reader.type_guards import is_str_list

ValueType: TypeAlias = (
    str | float | int | ScanType | list[str] | list[float] | list[int]
)


@define
class Attribute:
    name: str
    value: ValueType
    units: str | None = None

    def __str__(self) -> str:
        if self.name == "start_time" and self.units == "unix time":
            if is_float_or_float_list(self.value):
                value: ValueType = timestamp2str(self.value)
            else:
                raise TypeError
        else:
            value = self.value
        if isinstance(value, list):
            str_ = two_column_format(self.name, value, left_width=15)
        else:
            units = f" {self.units}" if self.units is not None else ""
            str_ = f"{self.name:15}{value}{units}"
        return str_

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def merge(cls, attributes: list[Attribute]) -> Attribute | None:
        if len(attributes) == 0:
            return None
        if len(attributes) == 1:
            return attributes[0]

        first_attr = attributes[0]
        names_eq = all(first_attr.name == a.name for a in attributes[1:])
        values_eq = all(first_attr.value == a.value for a in attributes[1:])
        units_eq = all(first_attr.units == a.units for a in attributes[1:])

        if names_eq and values_eq and units_eq:
            return attributes[0]
        elif (
            names_eq
            and units_eq
            and first_attr.name in ["filename", "start_time"]
        ):
            values = _list_values(attributes)
            return Attribute(
                name=first_attr.name,
                value=values,
                units=first_attr.units,
            )
        else:
            raise ValueError(f"Cannot merge attribute {attributes[0].name}")


def _list_values(attributes: list[Attribute]) -> list[str] | list[float]:
    value_list = [a.value for a in attributes]
    if is_float_list(value_list):
        return value_list
    elif is_str_list(value_list):
        return value_list
    else:
        raise TypeError
