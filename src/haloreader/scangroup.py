from __future__ import annotations

from enum import Enum, auto

import numpy as np

from haloreader.exceptions import UnexpectedInput
from haloreader.halo import Halo


class ScanGroup(Enum):
    STARE = auto()
    VAD = auto()
    UNCLASSIFIED = auto()

    @classmethod
    def from_halo(cls, halo: Halo | None) -> ScanGroup:
        if halo is None:
            return ScanGroup.UNCLASSIFIED
        elevation = halo.elevation.data
        azimuth = halo.azimuth.data
        if len(elevation) == 0 or len(azimuth) == 0:
            raise UnexpectedInput
        if np.isclose(elevation[0], 90.0) and np.allclose(elevation, elevation[0]):
            return ScanGroup.STARE
        if np.allclose(elevation, elevation[0]) and np.all(
            np.abs(np.diff(azimuth)) > 1
        ):
            return ScanGroup.VAD
        return ScanGroup.UNCLASSIFIED
