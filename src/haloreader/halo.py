from __future__ import annotations

import datetime
import logging
import re
from dataclasses import dataclass
from typing import Any, Protocol, TypeGuard, runtime_checkable

import netCDF4
import numpy as np

import haloreader.attenuated_backscatter_coefficient
import haloreader.background_correction
import haloreader.screen
from haloreader.metadata import Metadata
from haloreader.type_guards import is_fancy_index, is_ndarray, is_none_list
from haloreader.utils import CLOUDNET_TIME_UNIT_FMT, UNIX_TIME_FMT, UNIX_TIME_UNIT
from haloreader.variable import Variable, VariableWithNumpyData

log = logging.getLogger(__name__)


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
    beta_raw: Variable
    spectral_width: Variable | None = None
    intensity: Variable | None = None
    beta: Variable | None = None
    beta_screened: Variable | None = None
    doppler_velocity_screened: Variable | None = None

    def to_nc(
        self,
        nc_map: dict[str, dict] | None = None,
        nc_exclude: dict[str, set] | None = None,
    ) -> memoryview:
        nc = netCDF4.Dataset("inmemory.nc", "w", memory=1028)
        for attr_name in self.__dataclass_fields__.keys():
            halo_attr = getattr(self, attr_name)
            if halo_attr is not None:
                halo_attr.nc_write(nc, nc_map=nc_map, nc_exclude=nc_exclude)
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

    def remove_profiles_with_duplicate_time(self) -> None:
        if not is_ndarray(self.time.data):
            raise TypeError
        mask = _duplicate_time_mask(self.time.data)
        for attr_name in self.__dataclass_fields__.keys():
            halo_attr = getattr(self, attr_name)
            if (
                isinstance(halo_attr, Variable)
                and is_ndarray(halo_attr.data)
                and isinstance(halo_attr.dimensions, tuple)
                and self.time.name in halo_attr.dimensions
            ):
                index = tuple(
                    (
                        mask if d == self.time.name else slice(None)
                        for i, d in enumerate(halo_attr.dimensions)
                    )
                )
                if not is_fancy_index(index):
                    raise TypeError
                halo_attr.data = halo_attr.data[index]

    def convert_time_unit2cloudnet_time(self) -> None:
        _convert_timevar_unit2cloudnet_time(self.time)
        _convert_timevar_unit2cloudnet_time(self.metadata.start_time)

    def correct_background(self, halobg: HaloBg) -> None:
        if not is_ndarray(self.range.data):
            raise TypeError
        halobg_sliced = halobg.slice_range(len(self.range.data))
        p_amp = halobg_sliced.amplifier_noise()
        intensity_step1 = (
            haloreader.background_correction.background_measurement_correction(
                self.time,
                self.intensity_raw,
                halobg_sliced.time,
                halobg_sliced.background,
                p_amp,
            )
        )
        signalmask = haloreader.background_correction.threshold_signalmask(
            intensity_step1
        )
        self.intensity = haloreader.background_correction.snr_correction(
            intensity_step1, signalmask
        )

    def compute_beta(self) -> None:
        if not isinstance(self.intensity, Variable):
            raise TypeError
        log.warning("beta is computed using placeholder values")
        self.beta = haloreader.attenuated_backscatter_coefficient.compute_beta(
            self.intensity,
            self.range,
            self.metadata.focus_range,
            self.metadata.wavelength,
        )

    def compute_noise_screen(self) -> Variable:
        if not isinstance(self.intensity, Variable):
            raise TypeError
        return haloreader.screen.compute_noise_screen(
            self.intensity, self.doppler_velocity
        )

    def compute_beta_screened(self, screen: Variable) -> None:
        if not isinstance(self.beta, Variable):
            raise TypeError
        self.beta_screened = Variable(
            name="beta_screened",
            long_name="screened attenuated backscatter coefficient",
            comment=(
                "Experimental variable. Computed using uncalibrated/placeholder values."
            ),
            units="m-1 sr-1",
            dimensions=self.beta.dimensions,
            data=np.ma.masked_array(self.beta.data, mask=screen.data),
        )

    def compute_doppler_velocity_screened(self, screen: Variable) -> None:
        if not isinstance(self.beta, Variable):
            raise TypeError
        self.doppler_velocity_screened = Variable(
            name="doppler_velocity_screened",
            long_name="screened radial velocity (positive away from lidar)",
            units=self.doppler_velocity.units,
            dimensions=self.doppler_velocity.dimensions,
            data=np.ma.masked_array(self.doppler_velocity.data, mask=screen.data),
        )


def _convert_timevar_unit2cloudnet_time(var: Variable) -> None:
    """Converts time variable to cloudnet format.

    Format is: hours since [beginning of the day of the first
    measurement]
    """
    if not (is_ndarray(var.data) and len(var.data) > 0):
        return
    if not isinstance(var.units, str):
        raise TypeError
    if match_ := re.match(r"(seconds|hours) since (.*)", var.units):
        unit = match_.group(1)
        if not isinstance(unit, str):
            raise TypeError
        base = datetime.datetime.strptime(match_.group(2), UNIX_TIME_FMT)
        match unit:
            case "seconds" | "minutes" | "hours" | "weeks":
                tdelta = datetime.timedelta(**{unit: var.data[0]})  # type: ignore
            case other_unit:
                raise ValueError(f"Unexpected unit {other_unit}")
        new_base = (base + tdelta).replace(hour=0, minute=0, second=0, microsecond=0)
        base_diff = (base - new_base).total_seconds()
        scale = datetime.timedelta(**{unit: 1}).total_seconds()  # type: ignore
        new_time_in_hours = np.array([(base_diff + scale * t) / 3600 for t in var.data])
        new_unit = new_base.strftime(CLOUDNET_TIME_UNIT_FMT)
        var.data = new_time_in_hours
        var.units = new_unit
    else:
        raise NotImplementedError


def _sorted_halo_list_key(halo: Halo) -> float:
    if not is_ndarray(halo.metadata.start_time.data):
        raise TypeError
    if halo.metadata.start_time.units != UNIX_TIME_UNIT:
        raise ValueError(f"Unexpected time units: {halo.metadata.start_time.units}")
    if len(halo.metadata.start_time.data) != 1:
        raise ValueError
    start_time = halo.metadata.start_time.data[0]
    if not isinstance(start_time, float):
        raise TypeError
    return start_time


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

    def slice_range(self, slice_: int | slice) -> HaloBg:
        if isinstance(slice_, int):
            slice_ = slice(slice_)
        if not is_ndarray(self.time.data):
            raise TypeError
        if not is_ndarray(self.range.data):
            raise TypeError
        if not is_ndarray(self.background.data):
            raise TypeError
        return HaloBg(
            time=Variable.like(self.time, data=self.time.data),
            range=Variable.like(self.range, data=self.range.data[slice_]),
            background=Variable.like(
                self.background, data=self.background.data[:, slice_]
            ),
        )

    @classmethod
    def is_halobg_with_numpy_data(
        cls, halobg: HaloBg
    ) -> TypeGuard[HaloBgWithNumpyData]:
        return isinstance(halobg, HaloBgWithNumpyData)

    @classmethod
    def is_list_of_halobgs(cls, halobgs: list[Any]) -> TypeGuard[list[HaloBg]]:
        return all(isinstance(hbg, HaloBg) for hbg in halobgs)

    @classmethod
    def is_list_of_halobgs_with_numpy_data(
        cls, halobgs: list[Any]
    ) -> TypeGuard[list[HaloBgWithNumpyData]]:
        return all(isinstance(hbg, HaloBgWithNumpyData) for hbg in halobgs)

    @classmethod
    def merge(cls, halobgs: list[HaloBg]) -> HaloBg | None:
        if len(halobgs) == 0:
            return None
        if len(halobgs) == 1:
            return halobgs[0]

        if not HaloBg.is_list_of_halobgs_with_numpy_data(halobgs):
            raise TypeError
        nranges_med = np.median([hbg.range.data.shape[0] for hbg in halobgs]).astype(
            int
        )
        halobgs_filtered = [
            hbg for hbg in halobgs if hbg.range.data.shape[0] == nranges_med
        ]
        if not HaloBg.is_list_of_halobgs(halobgs_filtered):
            raise TypeError
        nignored = len(halobgs) - len(halobgs_filtered)
        if nignored > 0:
            log.warning(
                "Ignoring %d/%d background profiles (mismatching # of range gates)",
                nignored,
                len(halobgs),
            )
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
        if not HaloBg.is_halobg_with_numpy_data(self):
            raise TypeError
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


@runtime_checkable
class HaloBgWithNumpyData(Protocol):
    time: VariableWithNumpyData
    range: VariableWithNumpyData
    background: VariableWithNumpyData


def _sorted_halobg_list_key(halobg: HaloBg) -> float:
    if not is_ndarray(halobg.time.data):
        raise TypeError
    if halobg.time.units != UNIX_TIME_UNIT:
        raise ValueError
    if len(halobg.time.data) != 1:
        raise ValueError
    time = halobg.time.data[0]
    if not isinstance(time, float):
        raise TypeError
    return time


def _sorted_halobg_list(halobgs: list[HaloBg]) -> list[HaloBg]:
    return sorted(halobgs, key=_sorted_halobg_list_key)


def _is_increasing(time: np.ndarray) -> bool:
    return bool(np.all(np.diff(time) > 0))


def _duplicate_time_mask(time: np.ndarray) -> np.ndarray:
    _mask = np.isclose(np.diff(time), 0)
    nremoved = _mask.sum()
    if nremoved > 0:
        log.debug("Removed %d profiles (duplicate timestamps)", nremoved)
    return np.logical_not(np.insert(_mask, 0, False))
