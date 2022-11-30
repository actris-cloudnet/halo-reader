import argparse
import sys
from pathlib import Path

from halo_reader.debug import *
from halo_reader.read import read


def halo_dump() -> None:
    args = _halo_dump_parse_args()
    halo = read(src=args.src, src_bg=args.src_bg)
    if halo is None:
        return
    _halo_dump = str(halo)
    print(_halo_dump)


def _halo_dump_parse_args() -> argparse.Namespace:
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


def halo2nc() -> None:
    args = _halo2nc_parse_args()
    halo = read(src=args.src, src_bg=args.src_bg)
    if halo is not None:
        nc_buff = halo.to_nc()
        if args.output is not None:
            with args.output.open("wb") as f:
                f.write(nc_buff)
        else:
            sys.stdout.buffer.write(nc_buff)


def _halo2nc_parse_args() -> argparse.Namespace:
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
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
    )
    return parser.parse_args()
