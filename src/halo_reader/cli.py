import argparse
from pathlib import Path

from halo_reader.read import read


def hpl_dump() -> None:
    args = parse_args()
    read(src=args.src, src_bg=args.src_bg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "src", type=Path, nargs="*", default=[], help="raw .hpl file"
    )
    parser.add_argument(
        "--src-bg", type=Path, nargs="*", default=[], help="background file"
    )
    return parser.parse_args()
