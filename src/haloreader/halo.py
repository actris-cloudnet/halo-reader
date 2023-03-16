from __future__ import annotations

import logging
from dataclasses import dataclass
from pdb import set_trace as db
from typing import Any

import matplotlib.pyplot as plt
import netCDF4
import numpy as np

import haloreader.background_correction as bgc
from haloreader.background_correction import background_measurement_correction
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
    intensity_raw: Variable
    beta: Variable
    spectral_width: Variable | None = None
    intensity: Variable | None = None

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
        sorted_halos = _sorted_halo_list(halos)

        for attr_name in cls.__dataclass_fields__.keys():
            halo_attr_list = [getattr(h, attr_name) for h in sorted_halos]
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
            halo.remove_profiles_with_duplicate_time()
        if not _is_increasing(halo.time.data):
            raise ValueError("Time must be increasing")
        return halo

    def remove_profiles_with_duplicate_time(self):
        mask = _duplicate_time_mask(self.time.data)
        for attr_name in self.__dataclass_fields__.keys():
            halo_attr = getattr(self, attr_name)
            if (
                isinstance(halo_attr, Variable)
                and isinstance(halo_attr.dimensions, tuple)
                and self.time.name in halo_attr.dimensions
            ):
                index = tuple(
                    [
                        mask if d == self.time.name else slice(None)
                        for i, d in enumerate(halo_attr.dimensions)
                    ]
                )
                halo_attr.data = halo_attr.data[index]

    def correct_background(self, halobg: HaloBg) -> None:
        halobg_sliced = halobg.slice_range(len(self.range.data))
        p_amp = halobg_sliced.amplifier_noise()
        intensity_step1 = bgc.background_measurement_correction(
            self.time, self.intensity_raw, halobg_sliced.time, halobg_sliced.background, p_amp
        )
        cloudmask = bgc.threshold_cloudmask(intensity_step1)
        self.intensity = bgc.snr_correction(intensity_step1, cloudmask)


def _sorted_halo_list_key(halo: Halo):
    if halo.metadata.start_time.units != "unix time":
        raise ValueError
    if len(halo.metadata.start_time.data) != 1:
        raise ValueError
    return halo.metadata.start_time.data[0]


def _sorted_halo_list(halos: list[Halo]) -> list[Halo]:
    return sorted(halos, key=_sorted_halo_list_key)


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

    def slice_range(self, slice_: int | slice) -> None:
        if isinstance(slice_, int):
            slice_ = slice(slice_)
        return HaloBg(
            time=Variable.like(self.time, data=self.time.data),
            range=Variable.like(self.range, data=self.range.data[slice_]),
            background=Variable.like(
                self.background, data=self.background.data[:, slice_]
            ),
        )

    @classmethod
    def merge(cls, halobgs: list[HaloBg]) -> HaloBg | None:
        if len(halobgs) == 0:
            return None
        if len(halobgs) == 1:
            return halobgs[0]
        nranges_med = np.median([hbg.range.data.shape[0] for hbg in halobgs]).astype(int)
        halobgs_filtered = [hbg for hbg in halobgs if hbg.range.data.shape[0] == nranges_med]
        nignored = len(halobgs) - len(halobgs_filtered)
        if nignored > 0:
            logging.warning(f"Ignoring %d/%d background profiles (mismatching number of range gates)", nignored, len(halobgs))
        halobg_attrs: dict[str, Any] = {}
        sorted_halobgs = _sorted_halobg_list(halobgs_filtered)
        for attr_name in cls.__dataclass_fields__.keys():
            halobg_attr_list = [getattr(h, attr_name) for h in sorted_halobgs]
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

    def amplifier_noise(self) -> Variable:
        _sum_over_gates = self.background.data.sum(axis=1)
        _normalised_bg = self.background.data / _sum_over_gates[:, np.newaxis]
        return Variable(
            name="p_amp",
            long_name=(
                "Mean of normalised background over time. "
                "Profiles are normalised with sum over gates"
            ),
            dimensions=("range",),
            data=_normalised_bg.mean(axis=0),
        )


def _sorted_halobg_list_key(halobg: HaloBg):
    if halobg.time.units != "unix time":
        raise ValueError
    if len(halobg.time.data) != 1:
        raise ValueError
    return halobg.time.data[0]


def _sorted_halobg_list(halos: list[HaloBg]) -> list[HaloBg]:
    return sorted(halos, key=_sorted_halobg_list_key)


def _is_increasing(time: np.ndarray) -> bool:
    return bool(np.all(np.diff(time) > 0))


def _duplicate_time_mask(time: np.ndarray) -> np.ndarray:
    _mask = np.isclose(np.diff(time), 0)
    nremoved = _mask.sum()
    if nremoved > 0:
        logging.debug(f"Removed {nremoved} profiles (duplicate timestamps)")
    return np.logical_not(np.insert(_mask, 0, False))
