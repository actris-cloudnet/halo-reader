from __future__ import annotations

from dataclasses import dataclass

import netCDF4
import numpy as np
import numpy.typing as npt

from halo_reader.debug import *
from halo_reader.type_guards import is_ndarray_list
from halo_reader.utils import indent_str


@dataclass(slots=True)
class Variable:
    name: str
    standard_name: str | None = None
    long_name: str | None = None
    units: str | None = None
    dimensions: tuple[str, ...] | None = None
    data: npt.NDArray | None = None

    def nc_create_dimension(self, nc: netCDF4.Dataset) -> None:
        nc.createDimension(self.name, None)

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        nc_var = nc.createVariable(self.name, "f8", self.dimensions, zlib=True)
        nc_var.standard_name = (
            self.standard_name if self.standard_name is not None else ""
        )
        nc_var.long_name = self.long_name if self.long_name is not None else ""
        nc_var.units = self.units if self.units is not None else ""
        nc_var[:] = self.data if self.data is not None else []

    def __str__(self) -> str:
        indent = 4 * " "
        width = 15
        str_ = (
            self.name
            + " "
            + str(self.dimensions)
            + "\n"
            + indent
            + "standard name".ljust(width, " ")
            + str(self.standard_name)
            + "\n"
            + indent
            + "long name".ljust(width, " ")
            + str(self.long_name)
            + "\n"
            + indent
            + "units".ljust(width, " ")
            + str(self.units)
            + "\n"
        )
        if self.data is not None:
            data_str = np.array2string(self.data, threshold=5)
            data_indented = indent_str(data_str, width=2 * len(indent))
            str_ += indent + "data\n" + data_indented
        return str_

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def merge(cls, vars: list[Variable]) -> Variable | None:
        if len(vars) == 0:
            return None
        if len(vars) == 1:
            return vars[0]

        first_var = vars[0]
        names_eq = all(first_var.name == v.name for v in vars[1:])
        standard_names_eq = all(
            first_var.standard_name == v.standard_name for v in vars[1:]
        )
        long_names_eq = all(
            first_var.long_name == v.long_name for v in vars[1:]
        )
        units_eq = all(first_var.units == v.units for v in vars[1:])
        dimensions_eq = all(
            first_var.dimensions == v.dimensions for v in vars[1:]
        )

        if not all(
            (
                names_eq,
                standard_names_eq,
                long_names_eq,
                units_eq,
                dimensions_eq,
            )
        ):
            raise ValueError(f"Cannot merge {first_var.name}")

        data_list = [v.data for v in vars]
        if not is_ndarray_list(data_list):
            raise TypeError
        if first_var.name == "range":
            if _arrays_close(data_list):
                return first_var
            else:
                raise ValueError("Cannot merge: Unequal ranges")
        data = np.concatenate(data_list)
        return Variable(
            name=first_var.name,
            standard_name=first_var.standard_name,
            long_name=first_var.long_name,
            units=first_var.units,
            dimensions=first_var.dimensions,
            data=data,
        )


def _arrays_close(array_list: list[np.ndarray]) -> bool:
    if len(array_list) < 2:
        return True
    first_arr = array_list[0]
    return all(np.allclose(first_arr, arr) for arr in array_list)
