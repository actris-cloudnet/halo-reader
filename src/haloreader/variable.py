from __future__ import annotations

import copy
from dataclasses import dataclass
from pdb import set_trace as db
from typing import Any, TypeAlias, TypeGuard

import netCDF4
import numpy as np
from matplotlib.axes import Axes

from haloreader.exceptions import MergeError, NetCDFWriteError
from haloreader.type_guards import is_float_list, is_int_list, is_ndarray_list

DataType: TypeAlias = np.ndarray | int | float | None


@dataclass(slots=True)
class Variable:
    name: str
    standard_name: str | None = None
    long_name: str | None = None
    units: str | None = None
    dimensions: tuple[str, ...] | None = None
    data: DataType = None

    @classmethod
    def is_variable_list(cls, val: list[Any]) -> TypeGuard[list[Variable]]:
        return all(isinstance(x, Variable) for x in val)

    def nc_create_dimension(self, nc: netCDF4.Dataset) -> None:
        nc.createDimension(self.name, None)

    def nc_write(self, nc: netCDF4.Dataset) -> None:
        nc_dtype = _choose_nc_dtype(self)
        dimensions = self.dimensions if self.dimensions is not None else ()
        for dim in dimensions:
            if not _dimension_exists(nc, dim):
                nc.createDimension(dim, None)
        nc_var = nc.createVariable(self.name, nc_dtype, dimensions, zlib=True)
        nc_var.standard_name = (
            self.standard_name if self.standard_name is not None else ""
        )
        nc_var.long_name = self.long_name if self.long_name is not None else ""
        nc_var.units = self.units if self.units is not None else ""
        nc_var[:] = self.data if self.data is not None else []

    @classmethod
    def like(
        cls,
        var: Variable,
        data: DataType,
        name: str | None = None,
        standard_name: str | None = None,
        long_name: str | None = None,
        units: str | None = None,
        dimensions: tuple[str, ...] | None = None,
    ) -> Variable:
        # pylint: disable=too-many-arguments
        return Variable(
            name=name if name is not None else var.name,
            standard_name=standard_name
            if standard_name is not None
            else var.standard_name,
            long_name=long_name if long_name is not None else var.long_name,
            units=units if units is not None else var.units,
            dimensions=dimensions if dimensions is not None else var.dimensions,
            data=data,
        )

    @classmethod
    def merge(cls, vars_: list[Variable]) -> Variable | None:
        _check_merge(vars_)

        if len(vars_) == 0:
            return None
        if len(vars_) == 1:
            return vars_[0]
        first_var = vars_[0]

        if first_var.name == "range":
            data: DataType = _reduce_range(vars_)
        elif first_var.dimensions is None:
            data = _get_scalar_data(vars_)
        else:
            data = _concatenate_along_first_dimension(vars_)
        return Variable(
            name=first_var.name,
            standard_name=first_var.standard_name,
            long_name=first_var.long_name,
            units=first_var.units,
            dimensions=first_var.dimensions,
            data=data,
        )

    def plot(self, ax: Axes) -> None:  # type: ignore[no-any-unimported]
        if "intensity" in self.name:
            _plot_intensity(self, ax)
        elif "background" in self.name:
            _plot_background(self, ax)
        else:
            raise NotImplementedError


def _plot_intensity(var: Variable, ax: Axes) -> None:  # type: ignore[no-any-unimported]
    vdelta = 1e-3
    vmin, vmax = (1 - vdelta, 1 + vdelta)
    if not isinstance(var.data, np.ndarray):
        raise TypeError
    ax.imshow(
        var.data.T,
        origin="lower",
        vmin=vmin,
        vmax=vmax,
        aspect="auto",
        interpolation="none",
    )
    ax.set_title(var.name)


def _plot_background(  # type: ignore[no-any-unimported]
    var: Variable, ax: Axes
) -> None:
    if not isinstance(var.data, np.ndarray):
        raise TypeError
    mean = var.data.mean()
    std = var.data.std()
    vmin, vmax = (mean - std, mean + std)
    ax.imshow(
        var.data.T,
        origin="lower",
        vmin=vmin,
        vmax=vmax,
        aspect="auto",
        interpolation="none",
    )
    ax.set_title(var.name)


def _dimension_exists(nc: netCDF4.Dataset | None, dim: str) -> bool:
    if nc is None:
        return False
    if dim in nc.dimensions:
        return True
    return _dimension_exists(nc.parent, dim)


def _choose_nc_dtype(var: Variable) -> str:
    if var.data is None:
        return "f4"
    if isinstance(var.data, float):
        return "f4"
    if isinstance(var.data, int):
        return "i4"
    if isinstance(var.data, np.ndarray):
        if var.data.dtype.kind == "f":
            return "f4"
        if var.data.dtype.kind == "i":
            return "i4"
        raise NetCDFWriteError
    raise NetCDFWriteError


def _check_merge(vars_: list[Variable]) -> None:
    if len(vars_) < 2:
        return
    first_var = vars_[0]
    if not all(first_var.name == v.name for v in vars_[1:]):
        raise MergeError
    if not all(first_var.standard_name == v.standard_name for v in vars_[1:]):
        raise MergeError
    if not all(first_var.long_name == v.long_name for v in vars_[1:]):
        raise MergeError
    if not all(first_var.dimensions == v.dimensions for v in vars_[1:]):
        raise MergeError


def _get_scalar_data(vars_: list[Variable]) -> float | int:
    scalars = [v.data for v in vars_]
    if not (is_float_list(scalars) or is_int_list(scalars)):
        raise TypeError
    if _scalars_equal(scalars):
        return scalars[0]
    raise MergeError("Cannot merge unequal dimensionless scalars")


def _scalars_equal(scalars: list[float] | list[int]) -> bool:
    if len(scalars) < 2:
        return True
    if is_int_list(scalars):
        return all(s == scalars[0] for s in scalars[1:])
    return all(np.isclose(s, scalars[0]) for s in scalars[1:])


def _reduce_range(vars_: list[Variable]) -> np.ndarray:
    range_list = [v.data for v in vars_]
    if not is_ndarray_list(range_list):
        raise TypeError
    if not _array_shapes_equal(range_list):
        raise MergeError("Cannot merge, range shapes unequal")
    if _arrays_close(range_list):
        return range_list[0]
    raise MergeError("Cannot merge unequal ranges")


def _concatenate_along_first_dimension(vars_: list[Variable]) -> np.ndarray:
    _check_concat(vars_)
    data_list = [v.data for v in vars_]
    if is_ndarray_list(data_list):
        return np.concatenate(data_list)
    raise TypeError


def _check_concat(vars_: list[Variable]) -> None:
    if len(vars_) < 2:
        return
    first_var = vars_[0]
    if not isinstance(first_var.data, np.ndarray):
        raise TypeError
    if isinstance(first_var.dimensions, tuple):
        ndim = len(first_var.dimensions)
    else:
        raise TypeError
    data_list = [v.data for v in vars_]
    if not is_ndarray_list(data_list):
        raise MergeError
    if ndim < 1:
        raise MergeError
    if not all(ndim == np.ndim(data) for data in data_list):
        raise MergeError
    first_shape = first_var.data.shape
    if ndim > 1 and not all(first_shape[1:] == d.shape[1:] for d in data_list):
        raise MergeError


def _arrays_close(array_list: list[np.ndarray]) -> bool:
    if len(array_list) < 2:
        return True
    first_arr = array_list[0]
    return all(np.allclose(first_arr, arr) for arr in array_list)


def _array_shapes_equal(array_list: list[np.ndarray]) -> bool:
    if len(array_list) < 2:
        return True
    first_arr = array_list[0]
    return all(first_arr.shape == arr.shape for arr in array_list)
