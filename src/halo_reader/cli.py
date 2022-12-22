import argparse
import sys
from pathlib import Path

from halo_reader.read import read, read_bg


def halo2nc() -> None:
    args = _halo2nc_parse_args()
    halo = read(src_files=args.src)
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
        "-o",
        "--output",
        type=Path,
    )
    return parser.parse_args()


def halobg2nc() -> None:
    args = _halobg2nc_parse_args()
    halobg = read_bg(src_files=args.src)
    if halobg is not None:
        nc_buff = halobg.to_nc()
        if args.output is not None:
            with args.output.open("wb") as f:
                f.write(nc_buff)
        else:
            sys.stdout.buffer.write(nc_buff)


def _halobg2nc_parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "src", type=Path, nargs="*", default=[], help="background files"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
    )
    return parser.parse_args()
