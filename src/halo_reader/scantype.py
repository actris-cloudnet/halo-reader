from __future__ import annotations

import re
from enum import Enum, auto


class ScanType(Enum):
    STARE = auto()
    STARE_OVERLAPPING = auto()
    SECTORSCAN_STEPPED = auto()
    VAD = auto()
    VAD_STEPPED = auto()
    VAD_OVERLAPPING = auto()
    USER1_STEPPED = auto()
    USER1_CSM_OVERLAPPING = auto()
    USER2_STEPPED = auto()
    USER2_CSM = auto()
    WIND_PROFILE = auto()
    WIND_PROFILE_OVERLAPPING = auto()
    RHI = auto()

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def from_filename(cls, filename: str) -> ScanType | None:
        match_ = re.match("^([a-zA-Z0-9]+).*", filename)
        if match_:
            scantype_str = match_.group(1).upper()
            if scantype_str in cls.__members__:
                return ScanType[scantype_str]
        return None
