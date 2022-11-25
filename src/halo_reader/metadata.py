from attrs import define
from typing import Optional
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

