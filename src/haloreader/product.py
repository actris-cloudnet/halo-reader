from enum import Enum

class Product(Enum):
    STARE = "stare"
    WIND = "wind"

    def __str__(self) -> str:
        return self.value
