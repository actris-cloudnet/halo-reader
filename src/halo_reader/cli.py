from halo_reader.read import read
import argparse
from pathlib import Path


def hpl_dump():
    args = parse_args()
    read(src=args.src, src_bg = args.src_bg)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=Path, nargs="*",
                        default=[],
                        help="raw .hpl file")
    parser.add_argument("--src-bg", type=Path, nargs="*",
                        default=[],
                        help="background file")
    return parser.parse_args()
