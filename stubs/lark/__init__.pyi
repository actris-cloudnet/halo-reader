from typing import Callable

from halo_reader.attribute import Attribute
from halo_reader.metadata import Metadata
from halo_reader.transformer import HeaderTransformer
from halo_reader.variable import Variable

class Transformer: ...

class Lark:
    def __init__(
        self, grammar: str, transformer: HeaderTransformer, parser: str
    ): ...
    def parse(
        self, string: str
    ) -> tuple[
        Metadata,
        list[Variable],
        list[Variable],
        Callable[[Variable, Variable], Variable],
    ]: ...
