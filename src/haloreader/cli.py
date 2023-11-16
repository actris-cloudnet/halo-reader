import argparse
import datetime
import logging
from glob import glob
from pathlib import Path

import matplotlib.pyplot as plt

from haloboard.writer import Writer
from halodata.datasets import get_halo_cloudnet
from haloreader.read import read, read_bg
from haloreader.type_guards import is_ndarray

log = logging.getLogger(__name__)


def halo_reader() -> None:
    logging.basicConfig(level=logging.INFO)
    args = _haloreader_args()
    if args.subcommand == "from_cloudnet":
        _from_cloudnet(args)
    elif args.subcommand == "from_raw":
        _from_raw(args)
    else:
        raise NotImplementedError


def _from_cloudnet(args: argparse.Namespace) -> None:
    halo, halobg = get_halo_cloudnet(site=args.site, date=args.date)
    if halo is None:
        log.warning("No data from %s on %s", args.site, args.date)
        return
    if halobg is None:
        raise TypeError
    log.info("Correct background")
    halo.correct_background(halobg)
    log.info("Compute beta")
    halo.compute_beta()
    log.info("Compute noise screen")
    screen = halo.compute_noise_screen()
    log.info("Compute screened beta")
    halo.compute_beta_screened(screen)
    log.info("Compute screened doppler velocity")
    halo.compute_doppler_velocity_screened(screen)
    log.info("Convert timeunits")
    halo.convert_time_unit2cloudnet_time()
    log.info("Create netCDF")
    nc_buff = halo.to_nc()
    with open(f"halo_{args.site}_{args.date}.nc", "wb") as f:
        f.write(nc_buff)
    if args.plot:
        log.info("Create plots")
        writer = Writer()
        fig, ax = plt.subplots(nplots := 6, 1, figsize=(24, nplots * 6))
        halo.intensity_raw.plot(ax[0])
        halo.doppler_velocity.plot(ax[1])
        if halo.intensity is not None:
            halo.intensity.plot(ax[2])
        if halo.beta is not None:
            halo.beta.plot(ax[3])
        if halo.beta_screened is not None:
            halo.beta_screened.plot(ax[4])
        if halo.doppler_velocity_screened is not None:
            halo.doppler_velocity_screened.plot(ax[5])

        writer.add_figure(f"halo_{args.site}_{args.date}", fig)


def _parse_files_from_arg(path_list: list) -> list:
    allowed_wildcards = "*?"
    files = []
    for src in path_list:
        if any((c in allowed_wildcards) for c in src.name):
            wildcard_files = glob(src.name)
            if wildcard_files:
                for wildcard_file in wildcard_files:
                    files.append(Path(wildcard_file))
        else:
            files.append(src)
    return files


def _from_raw(args: argparse.Namespace) -> None:
    halo_src = [src for src in args.src if src.name.endswith(".hpl")]
    halo_src = _parse_files_from_arg(halo_src)
    bg_src = [
        src
        for src in args.src
        if src.name.startswith("Background") and src.name.endswith(".txt")
    ]
    bg_src = _parse_files_from_arg(bg_src)
    halo = read(halo_src)
    if halo is None:
        log.warning("No data")
        return

    halobg = read_bg(bg_src)
    if halobg:
        if not is_ndarray(halobg.background.data):
            raise TypeError
        if halobg.background.data.shape[0] < 300:
            log.warning(
                "Few (< 300) background profiles "
                "might lead to incorrect background correction"
            )
        halo.correct_background(halobg)
    else:
        log.warning("No background files, skipping background correction")
    nc_buff = halo.to_nc()
    with args.output.open("wb") as f:
        f.write(nc_buff)
    if args.plot:
        writer = Writer()
        fig, ax = plt.subplots(3, 1, figsize=(24, 16))
        halo.intensity_raw.plot(ax[0])
        halo.doppler_velocity.plot(ax[1])
        if halo.intensity:
            halo.intensity.plot(ax[2])
        writer.add_figure(f"{args.output.stem}", fig)


def _haloreader_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True
    )
    _from_cloudnet_args(
        subparsers.add_parser(
            "from_cloudnet", help="Download files directly from cloudnet."
        )
    )
    _from_raw_args(
        subparsers.add_parser(
            "from_raw", help="Read and background correct raw files into netCDF"
        )
    )

    return parser.parse_args()


def _from_cloudnet_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-p", "--plot", action="store_true")
    parser.add_argument("-s", "--site", type=str, default="warsaw")
    parser.add_argument(
        "-d",
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.date.today() - datetime.timedelta(days=1),
    )


def _from_raw_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-p", "--plot", action="store_true")
    parser.add_argument(
        "src",
        type=Path,
        nargs="*",
        default=[],
        help="Raw and background files in an arbitrary order",
    )
    parser.add_argument("-o", "--output", type=Path, required=True)
