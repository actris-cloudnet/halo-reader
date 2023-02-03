# pylint: disable=C0103
import re
from datetime import datetime, timezone
from typing import Any, Callable

import lark
import numpy as np

from .attribute import Attribute
from .metadata import Metadata
from .scantype import ScanType
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
        return Variable(name="ngates", data=val)

    def npulses(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="npulses", data=val)

    def nrays(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="nrays", data=val)

    def nwaypoints(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="nwaypoints", data=val)

    def scantype(self, children: list) -> Attribute:
        val, *_ = children
        return Attribute(name="scantype", value=val)

    def focus_range(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="focus_range", data=val)

    def gate_range(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="gate_range", data=val, units="m")

    def gate_length(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="gate_length", data=val, units="pts")

    def resolution(self, children: list) -> Variable:
        val, *_ = children
        return Variable(name="resolution", data=val, units="m/s")

    def end_of_header_with_instrument_spectral_width(
        self, children: list
    ) -> Variable:
        val, *_ = children
        return Variable(name="instrument_spectral_width", data=val)

    def start_time(self, children: list) -> dict:
        time_str, *_ = children
        match_ = re.match(
            r"(\d{4})(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str
        )
        if match_ is None:
            raise NotImplementedError(
                f"Parse for fmt {time_str} not implemented yet"
            )
        return {
            "start_time": Variable(
                name="start_time",
                units="unix time",
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

    def range_of_measurement(self, children: list) -> dict:
        func, *_ = children
        return {"range_func": func}

    def RANGE_OF_MEASUREMENT(
        self, _: Any
    ) -> Callable[[Variable, Variable], Variable]:
        return range_func

    time_dimension_variables = lambda self, vars: {"time_vars": vars}

    def time_dimension_variable(self, children: list) -> Variable:
        var, *_ = children
        if not isinstance(var, Variable):
            raise TypeError
        return var

    time_range_dimension_variables = lambda self, vars: {
        "time_range_vars": vars
    }

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
        name="azimuth", units="degrees", dimensions=("time",)
    )
    ELEVATION_DEG = lambda self, _: Variable(
        name="elevation", units="degrees", dimensions=("time",)
    )
    PITCH_DEG = lambda self, _: Variable(
        name="pitch", units="degrees", dimensions=("time",)
    )
    ROLL_DEG = lambda self, _: Variable(
        name="roll", units="degrees", dimensions=("time",)
    )

    RANGE_GATE = lambda self, _: Variable(
        name="range", dimensions=("time", "range")
    )
    DOPPLER = lambda self, _: Variable(
        name="doppler_velocity", units="m/s", dimensions=("time", "range")
    )
    INTENSITY = lambda self, _: Variable(
        name="intensity", units="snr+1", dimensions=("time", "range")
    )
    BETA = lambda self, _: Variable(
        name="beta", units="m-1 sr-1", dimensions=("time", "range")
    )
    SPECTRAL_WIDTH = lambda self, _: Variable(
        name="spectral_width", dimensions=("time", "range")
    )

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
    WIND_PROFILE_OVERLAPPING = (
        lambda self, _: ScanType.WIND_PROFILE_OVERLAPPING
    )
    RHI = lambda self, _: ScanType.RHI

    STRING = lambda self, _: _.value
    INTEGER = lambda self, _: int(_.value)
    DECIMAL = lambda self, _: float(_.value)


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
        dimensions=("range",),
        units=gate_range.units,
        data=range_,
    )
