from pathlib import Path
from .debug import *
from io import BufferedReader
from .exceptions import HeaderNotFound
from .transformer import HeaderTransformer
import lark
import pkgutil

grammar_header = pkgutil.get_data("halo_reader", "grammar_header.lark")
if not isinstance(grammar_header, bytes):
    raise FileNotFoundError("Header grammar file not found")
parser = lark.Lark(grammar_header.decode(),parser="lalr", transformer=HeaderTransformer())


def read(src: list[Path], src_bg: list[Path]) -> None:
    for i,s in enumerate(src):
        header_end, header_bytes = _read_header(s)
        tree = parser.parse(header_bytes.decode())
        return

def _read_header(src: Path) -> tuple[int, bytes]:
    with src.open("rb") as f:
        header_end = _find_header_end(f)
        if header_end < 0:
            raise HeaderNotFound
        header_bytes = f.read(header_end)
    return header_end, header_bytes
        
def _find_header_end(f: BufferedReader) -> int:
    guess = 1024
    loc_end = _try_header_end(f,guess)
    if loc_end < 0:
        loc_end = _try_header_end(f,2*guess)
    return loc_end

def _try_header_end(f: BufferedReader, guess: int) -> int:
    pos = f.tell()
    fbytes = f.read(guess)
    f.seek(pos)
    loc_sep = fbytes.find(b"****")
    if loc_sep < 0:
        return -1
    loc_end = fbytes.find(b"\r\n",loc_sep)
    if loc_end >= 0:
        loc_end += 2
    return loc_end
    



