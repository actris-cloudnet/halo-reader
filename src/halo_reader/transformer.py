import re
from datetime import datetime, timezone
from typing import Any, Callable

import lark
import numpy as np
import numpy.typing as npt

from .attribute import Attribute
from .debug import *
from .metadata import Metadata
from .scantype import ScanType
from .variable import Variable


class HeaderTransformer(lark.Transformer):
    def __init__(self) -> None:
        super(HeaderTransformer, self).__init__()
        keyval_attrs = [
            "filename",
            "system_id",
            "ngates",
            "npulses",
            "nrays",
            "nwaypoints",
            "scantype",
            "focus_range",
        ]
        for key in keyval_attrs:
            setattr(self, key, keyvalfunc(key))
        unit_attrs = [
            ("gate_range", "m"),
            ("gate_length", "pts"),
            ("resolution", "m/s"),
        ]
        for key, unit in unit_attrs:
            setattr(self, key, unitfunc(key, unit))

    def header(
        self, children: list
    ) -> tuple[
        Metadata,
        list[Variable],
        list[Variable],
        Callable[[Variable, Attribute], Variable],
    ]:
        _header = {}
        for c in children:
            if isinstance(c, dict):
                _header.update(c)
            else:
                raise TypeError
        time_vars = _header.pop("time_vars")
        time_range_vars = _header.pop("time_range_vars")
        range_func = _header.pop("range_func")
        metadata = Metadata(**_header)
        return metadata, time_vars, time_range_vars, range_func

    def start_time(self, children: list) -> dict:
        time_str, *_ = children
        time_fmt1 = re.match(
            r"(\d{4})(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str
        )
        if time_fmt1:
            dt = _time_fmt1_to_datetime(time_fmt1)
        else:
            raise NotImplementedError(
                f"Parse for fmt {time_str} not implemented yet"
            )
        return {
            "start_time": Attribute(
                name="start_time", units="unix time", value=dt.timestamp()
            )
        }

    def range_of_measurement(self, children: list) -> dict:
        func, *_ = children
        return {"range_func": func}

    def RANGE_OF_MEASUREMENT(
        self, _: Any
    ) -> Callable[[Variable, Attribute], Variable]:
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


def keyvalfunc(key: str) -> Callable[[list], dict]:
    def _func(children: list) -> dict[str, Attribute]:
        val, *_ = children
        return {key: Attribute(name=key, value=val)}

    return _func


def unitfunc(key: str, units: str) -> Callable[[list], dict]:
    def _func(children: list) -> dict[str, Attribute]:
        val, *_ = children
        return {key: Attribute(name=key, value=val, units=units)}

    return _func


def range_func(range: Variable, gate_range: Attribute) -> Variable:
    if not isinstance(range.data, np.ndarray) or not isinstance(
        gate_range.value, float
    ):
        raise TypeError
    range_ = (range.data[0, :] + 0.5) * gate_range.value
    if not isinstance(range_, np.ndarray):
        raise TypeError
    return Variable(
        name="range",
        dimensions=("range",),
        units=gate_range.units,
        data=range_,
    )


def _time_fmt1_to_datetime(m: re.Match) -> datetime:
    return datetime(
        year=int(m.group(1)),
        month=int(m.group(2)),
        day=int(m.group(3)),
        hour=int(m.group(4)),
        minute=int(m.group(5)),
        second=int(m.group(6)),
        microsecond=int(m.group(7).ljust(6, "0")),
        tzinfo=timezone.utc,
    )
