from typing import Optional

from attrs import define


@define
class Attribute:
    name: str
    value: str | float | int
    units: Optional[str] = None

    def __str__(self) -> str:
        if self.units is not None:
            return f"{self.name:15}{self.value} {self.units}"
        else:
            return f"{self.name:15}{self.value}"

    def __repr__(self) -> str:
        return f"Attr[{str(self)}]"
