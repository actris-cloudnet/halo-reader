from typing import Optional

import numpy.typing as npt
from attrs import define


@define
class Variable:
    name: str
    standard_name: Optional[str] = None
    long_name: Optional[str] = None
    units: Optional[str] = None
    dimensions: Optional[tuple[str, ...]] = None
    data: Optional[npt.NDArray] = None

    def __str__(self) -> str:
        return f"{self.name} [{self.units}] {self.dimensions}"

    def __repr__(self) -> str:
        return f"Var[{self}]"
