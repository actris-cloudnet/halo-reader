from typing import Callable

from haloreader.attribute import Attribute
from haloreader.metadata import Metadata
from haloreader.transformer import HeaderTransformer
from haloreader.variable import Variable

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
