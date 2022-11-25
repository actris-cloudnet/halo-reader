import lark
import numpy.typing as npt
import re
from datetime import datetime
from .debug import *
from .attribute import Attribute
from .scantype import ScanType
from .variable import Variable
from .metadata import Metadata

class HeaderTransformer(lark.Transformer):
    def __init__(self):
        super(HeaderTransformer,self).__init__()
        keyval_attrs = [ "filename", "system_id", "ngates", "npulses", "nrays","scantype", "focus_range"]
        for key in keyval_attrs:
            setattr(self, key, keyvalfunc(key))
        unit_attrs = [
                    ("gate_range", "m"),
                    ("gate_length", "pts"),
                    ("resolution", "m/s"),
                ]
        for key, unit in unit_attrs:
            setattr(self, key, unitfunc(key, unit))
    def header(self, children: list):
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

    def start_time(self, children: list):
        time_str, *_ = children
        time_fmt1 = re.match(r"(\d{4})(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{2})", time_str)
        if time_fmt1:
            dt =  _time_fmt1_to_datetime(time_fmt1)
        else:
            raise NotImplementedError(f"Parse for fmt {time_str} not implemented yet")
        return {"start_time": Attribute(name="start_time", units="unix time", value=dt.timestamp())}
    
    def altitude_of_measurement(self, children: list) -> dict:
        func, *_ = children
        return {"range_func": func}

    def ALTITUDE_OF_MEASUREMENT(self, _: lark.lexer.Token):
        return range_func
    
    time_dimension_variables = lambda self, vars: {"time_vars": vars}

    def time_dimension_variable(self,children: list):
        var, *_ = children
        return var

    time_range_dimension_variables = lambda self, vars: {"time_range_vars": vars}

    def time_range_dimension_variable(self,children: list):
        var, *_ = children
        return var

    DECIMAL_TIME_H = lambda self, _: Variable(name="time", units="hours", dimensions=("time",), long_name="decimal time")
    AZIMUTH_DEG = lambda self, _: Variable(name="azimuth", units="degrees", dimensions=("time",))
    ELEVATION_DEG = lambda self, _: Variable(name="elevation", units="degrees", dimensions=("time",))
    PITCH_DEG = lambda self, _: Variable(name="pitch", units="degrees", dimensions=("time",))
    ROLL_DEG = lambda self, _: Variable(name="roll", units="degrees", dimensions=("time",))

    RANGE_GATE = lambda self, _: Variable(name="range", dimensions=("time","range"))
    DOPPLER = lambda self, _: Variable(name="doppler_velocity",units="m/s", dimensions=("time","range"))
    INTENSITY = lambda self, _: Variable(name="intensity",units="snr+1", dimensions=("time","range"))
    BETA = lambda self, _: Variable(name="beta",units="m-1 sr-1", dimensions=("time","range"))

    SCANTYPE = lambda self, _: ScanType[_.upper()] 
    STRING = lambda self, _: _.value
    INTEGER = lambda self, _: int(_.value)
    DECIMAL = lambda self, _: float(_.value)

def keyvalfunc(key: str):
    def _func(children: list):
        val, *_ = children
        return {key: Attribute(name=key, value= val)}
    return _func

def unitfunc(key: str, units: str):
    def _func(children: list):
        val, *_ = children
        return {key: Attribute(name=key, value=val, units=units)}
    return _func

def range_func(range: Variable, gate_range: Variable ) -> Variable:
    raise NotImplementedError
    return Variable(name="height")

def _time_fmt1_to_datetime(m: re.Match) -> datetime:
    return datetime(
            year = int(m.group(1)),
            month = int(m.group(2)),
            day = int(m.group(3)),
            hour = int(m.group(4)),
            minute = int(m.group(5)),
            second = int(m.group(6)),
            microsecond = int(m.group(7).ljust(6,"0")),
            )


