import argparse
from pathlib import Path

from halo_reader.read import read
from halo_reader.debug import *


def halo_dump() -> None:
    args = parse_args()
    halo = read(src=args.src, src_bg=args.src_bg)
    if halo is None:
        return
    _halo_dump = str(halo)
    print(_halo_dump)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "src", type=Path, nargs="*", default=[], help="raw hpl file"
    )
    parser.add_argument(
        "--src-bg",
        type=Path,
        nargs="*",
        default=[],
        help="background file [NOT IMPLEMENTED YET]",
    )
    return parser.parse_args()
