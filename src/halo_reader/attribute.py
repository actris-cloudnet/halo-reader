from attrs import define
from typing import Optional

@define
class Attribute:
    name: str
    value: str | float | int
    units: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.name}: {self.value} [{self.units}]"
    def __repr__(self) -> str:
        return f"Attr[{str(self)}]"

