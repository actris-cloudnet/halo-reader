from __future__ import annotations

from dataclasses import dataclass
from pdb import set_trace as db
from typing import Any

import netCDF4
import numpy as np

from haloreader.metadata import Metadata
from haloreader.type_guards import is_none_list
from haloreader.variable import Variable


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
        raise TypeError

    @classmethod
    def merge(cls, halos: list[Halo]) -> Halo | None:
        if len(halos) == 0:
            return None
        if len(halos) == 1:
            return halos[0]
        halo_attrs: dict[str, Any] = {}
        for attr_name in cls.__dataclass_fields__.keys():
            halo_attr_list = [getattr(h, attr_name) for h in halos]
            if Metadata.is_metadata_list(halo_attr_list):
                halo_attrs[attr_name] = Metadata.merge(halo_attr_list)
            elif Variable.is_variable_list(halo_attr_list):
                halo_attrs[attr_name] = Variable.merge(halo_attr_list)
            elif is_none_list(halo_attr_list):
                halo_attrs[attr_name] = None
            else:
                raise TypeError

        halo = Halo(**halo_attrs)
        if not isinstance(halo.time.data, np.ndarray):
            raise TypeError
        if not _is_increasing(halo.time.data):
            raise ValueError("Time must be increasing")
        return halo


@dataclass(slots=True)
class HaloBg:
    time: Variable
    range: Variable
    background: Variable

    def to_nc(self) -> memoryview:
        nc = netCDF4.Dataset("inmemory.nc", "w", memory=1028)
        self.time.nc_create_dimension(nc)
        self.range.nc_create_dimension(nc)
        for attr_name in self.__dataclass_fields__.keys():
            halobg_attr = getattr(self, attr_name)
            if halobg_attr is not None:
                halobg_attr.nc_write(nc)
        nc_buf = nc.close()
        if isinstance(nc_buf, memoryview):
            return nc_buf
        raise TypeError

    @classmethod
    def merge(cls, halobgs: list[HaloBg]) -> HaloBg | None:
        if len(halobgs) == 0:
            return None
        if len(halobgs) == 1:
            return halobgs[0]
        halobg_attrs: dict[str, Any] = {}
        for attr_name in cls.__dataclass_fields__.keys():
            halobg_attr_list = [getattr(h, attr_name) for h in halobgs]
            if Variable.is_variable_list(halobg_attr_list):
                halobg_attrs[attr_name] = Variable.merge(halobg_attr_list)
            elif is_none_list(halobg_attr_list):
                halobg_attrs[attr_name] = None
            else:
                raise TypeError
        halobg = HaloBg(**halobg_attrs)
        if not isinstance(halobg.time.data, np.ndarray):
            raise TypeError
        if not _is_increasing(halobg.time.data):
            raise ValueError("Time must be increasing")
        return halobg

    @classmethod
    def is_bgfilename(cls, filename: str) -> bool:
        return filename.lower().startswith("background_")

    def p_amplifier(self, normalise: bool = False) -> Variable:
        if normalise:
            _sum_over_gates = self.background.data.sum(axis=1)
            _normalised_bg = (
                self.background.data / _sum_over_gates[:, np.newaxis]
            )
            return Variable(
                name="p_amp",
                long_name=(
                    "Mean of normalised background over time. "
                    "Profiles are normalised with sum over gates"
                ),
                dimensions=("range",),
                data=_normalised_bg.mean(axis=0),
            )
        else:
            return Variable(
                name="p_amp",
                long_name="Mean of background over time",
                dimensions=("range",),
                data=self.background.data.mean(axis=0),
            )

    def p_amplifier_std(self, normalise: bool = False) -> Variable:
        if normalise:
            _sum_over_gates = self.background.data.sum(axis=1)
            _normalised_bg = (
                self.background.data / _sum_over_gates[:, np.newaxis]
            )
            return Variable(
                name="p_amp_std",
                long_name=(
                    "Std of normalised background over time. "
                    "Profiles are normalised with sum over gates"
                ),
                dimensions=("range",),
                data=_normalised_bg.std(axis=0),
            )
        else:
            return Variable(
                name="p_amp_std",
                long_name="Std of background over time",
                dimensions=("range",),
                data=self.background.data.std(axis=0),
            )


def _is_increasing(time: np.ndarray) -> bool:
    return bool(np.all(np.diff(time) > 0))
