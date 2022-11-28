from typing import Optional

import numpy.typing as npt
from attrs import define

from halo_reader.variable import Variable
from halo_reader.metadata import Metadata

@define
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
