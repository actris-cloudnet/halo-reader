from enum import Enum, auto

class ScanType(Enum):
    STARE = auto()

    def __str__(self) -> str:
        return str(self.name)
    def __repr__(self) -> str:
        return str(self)
