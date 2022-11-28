
from attrs import define

from .attribute import Attribute


@define
class Metadata:
    filename: Attribute
    system_id: Attribute
    ngates: Attribute
    gate_range: Attribute
    gate_length: Attribute
    npulses: Attribute
    nrays: Attribute
    scantype: Attribute
    focus_range: Attribute
    start_time: Attribute
    resolution: Attribute

    def __str__(self) -> str:
        _str = ""
        for _attr in self.__attrs_attrs__:
            attr = getattr(self, getattr(_attr, "name"))
            _str += f"{attr}\n"
        return _str
    def __repr__(self) -> str:
        return str(self)
