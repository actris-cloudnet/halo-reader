from halo_reader.read import read
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("src", type=Path, nargs="*",
                    help="raw .hpl file")
parser.add_argument("--src-bg", type=Path, nargs="*",
                    help="background file")
args = parser.parse_args()

read(src=args.src, src_bg = args.src_bg)


