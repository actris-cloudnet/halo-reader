# pylint: disable=C0103
import re
from datetime import datetime, timezone
from typing import Any, Callable

import lark
import numpy as np

from .attribute import Attribute
from .metadata import Metadata
from .scantype import ScanType
from .utils import UNIX_TIME_UNIT
from .variable import Variable


class HeaderTransformer(lark.Transformer):
    def header(
        self, children: list
    ) -> tuple[
        Metadata,
        list[Variable],
        list[Variable],
        Callable[[Variable, Variable], Variable],
    ]:
        _header = {}
        for child in children:
            if isinstance(child, dict):
                _header.update(child)
            elif isinstance(child, (Attribute, Variable)):
                _header[child.name] = child
            else:
                raise TypeError
        time_vars = _header.pop("time_vars")
        time_range_vars = _header.pop("time_range_vars")
        range_func_ = _header.pop("range_func")
        metadata = Metadata(**_header)
        return metadata, time_vars, time_range_vars, range_func_

    def filename(self, children: list) -> Attribute:
        val, *_ = children
        return Attribute(name="filename", value=val)

    def system_id(self, children: list) -> Attribute:
        val, *_ = children
        return Attribute(name="system_id", value=val)

    def ngates(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="ngates", long_name="number of gates", data=val)

    def npulses(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="npulses", long_name="number of pulses", data=val)

    def nrays(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="nrays", long_name="number of rays", data=val)

    def nwaypoints(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="nwaypoints", long_name="number of waypoints", data=val)

    def scantype(self, children: list) -> Attribute:
        val, *_ = children
        return Attribute(name="scantype", value=val)

    def focus_range(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="focus_range", long_name="focus range", data=val)

    def gate_range(self, children: list) -> Variable:
        val, *_ = children
        return Variable(
            name="gate_range", long_name="length of a gate", data=val, units="m"
        )

    def gate_length(self, children: list) -> Variable:
        val, *_ = children
        return Variable(
            name="gate_length",
            long_name="number of points per gate",
            data=val,
            units="1",
        )

    def resolution(self, children: list) -> Variable:
        val, *_ = children
        return Variable(
            name="resolution",
            long_name="resolution of the doppler velocity",
            data=val,
            units="m/s",
        )

    def end_of_header_with_instrument_spectral_width(self, children: list) -> Variable:
        val, *_ = children
        return Variable(
            name="instrument_spectral_width",
            long_name="instrument spectral width",
            units="1",
            data=val,
        )

    def start_time(self, children: list) -> dict:
        time_str, *_ = children
        if match_ := re.match(
            r"(\d{4})(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str
        ):
            return {
                "start_time": Variable(
                    name="start_time",
                    long_name="start times of individual raw files",
                    units=UNIX_TIME_UNIT,
                    calendar="standard",
                    dimensions=("start_time",),
                    data=np.array(
                        [
                            datetime(
                                year=int(match_.group(1)),
                                month=int(match_.group(2)),
                                day=int(match_.group(3)),
                                hour=int(match_.group(4)),
                                minute=int(match_.group(5)),
                                second=int(match_.group(6)),
                                microsecond=int(match_.group(7).ljust(6, "0")),
                                tzinfo=timezone.utc,
                            ).timestamp()
                        ]
                    ),
                )
            }
        raise NotImplementedError(f"Parse for fmt {time_str} not implemented yet")

    def range_of_measurement(self, children: list) -> dict:
        func, *_ = children
        return {"range_func": func}

    def RANGE_OF_MEASUREMENT(self, _: Any) -> Callable[[Variable, Variable], Variable]:
        return range_func

    time_dimension_variables = lambda self, vars: {"time_vars": vars}

    def time_dimension_variable(self, children: list) -> Variable:
        var, *_ = children
        if not isinstance(var, Variable):
            raise TypeError
        return var

    time_range_dimension_variables = lambda self, vars: {"time_range_vars": vars}

    def time_range_dimension_variable(self, children: list) -> Variable:
        var, *_ = children
        if not isinstance(var, Variable):
            raise TypeError
        return var

    DECIMAL_TIME_H = lambda self, _: Variable(
        name="time",
        units="hours",
        dimensions=("time",),
        long_name="decimal time",
    )
    AZIMUTH_DEG = lambda self, _: Variable(
        name="azimuth",
        long_name="azimuth from north",
        units="degrees",
        dimensions=("time",),
    )
    ELEVATION_DEG = lambda self, _: Variable(
        name="elevation",
        long_name="elevation from horizontal",
        units="degrees",
        dimensions=("time",),
    )
    PITCH_DEG = lambda self, _: Variable(
        name="pitch",
        long_name="pitch offset of the instrument",
        units="degrees",
        dimensions=("time",),
    )
    ROLL_DEG = lambda self, _: Variable(
        name="roll",
        long_name="roll offset of the instrument",
        units="degrees",
        dimensions=("time",),
    )

    RANGE_GATE = lambda self, _: Variable(
        name="range", long_name="index of the gate", dimensions=("time", "range")
    )
    DOPPLER = lambda self, _: Variable(
        name="doppler_velocity",
        long_name="radial velocity (positive away from lidar)",
        units="m s-1",
        dimensions=("time", "range"),
    )
    INTENSITY = lambda self, _: Variable(
        name="intensity_raw",
        long_name="raw intensity (signal-to-noise ratio + 1)",
        units="1",
        dimensions=("time", "range"),
    )
    BETA = lambda self, _: Variable(
        name="beta_raw",
        long_name="raw beta from instrument",
        units="m-1 sr-1",
        dimensions=("time", "range"),
    )
    # spectral width variable is also defined in
    # src/haloreader/data_reader/data_reader.pyx
    SPECTRAL_WIDTH = lambda self, _: spectral_width_factory()

    def scantype_enum(self, children: list[ScanType]) -> ScanType:
        val, *_ = children
        return val

    STARE = lambda self, _: ScanType.STARE
    STARE_OVERLAPPING = lambda self, _: ScanType.STARE_OVERLAPPING
    SECTORSCAN_STEPPED = lambda self, _: ScanType.SECTORSCAN_STEPPED
    VAD = lambda self, _: ScanType.VAD
    VAD_STEPPED = lambda self, _: ScanType.VAD_STEPPED
    VAD_OVERLAPPING = lambda self, _: ScanType.VAD_OVERLAPPING
    USER1_STEPPED = lambda self, _: ScanType.USER1_STEPPED
    USER1_CSM_OVERLAPPING = lambda self, _: ScanType.USER1_CSM_OVERLAPPING
    USER2_STEPPED = lambda self, _: ScanType.USER2_STEPPED
    USER2_CSM = lambda self, _: ScanType.USER2_CSM
    WIND_PROFILE = lambda self, _: ScanType.WIND_PROFILE
    WIND_PROFILE_OVERLAPPING = lambda self, _: ScanType.WIND_PROFILE_OVERLAPPING
    RHI = lambda self, _: ScanType.RHI
    S_VAD_70_STEPPED = lambda self, _: ScanType.S_VAD_70_STEPPED
    S_12_STARE_STEPPED = lambda self, _: ScanType.S_12_STARE_STEPPED

    STRING = lambda self, _: _.value
    INTEGER = lambda self, _: int(_.value)
    DECIMAL = lambda self, _: float(_.value)


def spectral_width_factory() -> Variable:
    return Variable(
        name="spectral_width",
        long_name="spectral width",
        units="1",
        dimensions=("time", "range"),
    )


def range_func(range_var: Variable, gate_range: Variable) -> Variable:
    if not isinstance(range_var.data, np.ndarray) or not isinstance(
        gate_range.data, float
    ):
        raise TypeError
    range_ = (range_var.data[0, :] + 0.5) * gate_range.data
    if not isinstance(range_, np.ndarray):
        raise TypeError
    return Variable(
        name="range",
        long_name="range of measurement from the instrument",
        dimensions=("range",),
        units=gate_range.units,
        data=range_,
    )
