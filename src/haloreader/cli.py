import argparse
import datetime
import logging
import re
from enum import Enum
from pathlib import Path
from itertools import islice

import matplotlib.pyplot as plt
import numpy as np

from haloboard.writer import Writer
from halodata.datasets import (
    get_halo_cloudnet,
    get_model_cloudnet,
    get_site_cloudnet,
    raw_cloudnet,
)
from haloreader.product import Product
from haloreader.read import read, read_bg
from haloreader.scangroup import ScanGroup
from haloreader.type_guards import is_ndarray
from haloreader.variable import Variable

log = logging.getLogger(__name__)


def halo_reader() -> None:
    logging.basicConfig(level=logging.INFO)
    args = _haloreader_args()
    if args.subcommand == "from_cloudnet":
        _from_cloudnet(args)
    elif args.subcommand == "from_raw":
        _from_raw(args)
    elif args.subcommand == "print_raw_from_cloudnet":
        _print_raw_from_cloudnet(args)
    else:
        raise NotImplementedError


def _from_cloudnet(args: argparse.Namespace) -> None:
    match args.product:
        case Product.WIND:
            _process_wind(args)
        case _:
            _process_stare(args)


def _red(s: str):
    return f"\033[91m{s}\033[0m"


def _blue(s: str):
    return f"\033[34m{s}\033[0m"


def _yellow(s: str):
    return f"\033[33m{s}\033[0m"


def _print_raw_from_cloudnet(args: argparse.Namespace) -> None:
    data = raw_cloudnet(args.site, args.date)
    for record, file in data:
        fname = record["filename"]
        if (
            args.include_fname_regexp is not None
            and re.match(args.include_fname_regexp, fname) is None
        ):
            continue
        if (
            args.exclude_fname_regexp is not None
            and re.match(args.exclude_fname_regexp, fname) is not None
        ):
            continue
        print(_red(record["filename"]), _blue(args.site), _yellow(str(args.date)))
        for i, line in islice(enumerate(file),args.nlines):
            print(line.decode().strip())


def _process_wind(args: argparse.Namespace) -> None:
    log.info(f"Processing wind {args.site} {args.date}")
    halo, halobg = get_halo_cloudnet(
        site=args.site, date=args.date, product=Product.WIND
    )
    site = get_site_cloudnet(args.site)
    if halo is None:
        log.warning("No data from %s on %s", args.site, args.date)
        return
    writer = Writer()
    nplots = 2 * 5 - 1
    nc_model = get_model_cloudnet(args.site, args.date)
    if nc_model is None:
        raise TypeError

    fig, ax = plt.subplots(nplots, 1, figsize=(24, nplots * 6))

    model_zonal = Variable.from_nc(nc_model, "uwind")
    model_meridional = Variable.from_nc(nc_model, "vwind")
    model_vertical = Variable.from_nc(nc_model, "wwind")
    mspeed = np.sqrt(model_zonal.data**2 + model_meridional.data**2)
    mdirec = np.arctan2(model_zonal.data, model_meridional.data)
    mdirec[mdirec < 0] += 2 * np.pi
    mspeed = Variable(
        name="horizontal_wind_speed_model",
        dimensions=model_zonal.dimensions,
        units=model_zonal.units,
        data=mspeed,
    )
    mdirec = Variable(
        name="horizontal_wind_direction",
        dimensions=model_zonal.dimensions,
        units="degrees",
        data=np.degrees(mdirec),
    )

    mheight = Variable.from_nc(nc_model, "height")
    mtime = Variable.from_nc(nc_model, "time")

    wind = halo.compute_wind()
    site_altitude = site.get("altitude")
    if isinstance(site_altitude, (float, int)):
        wind.height = Variable(
            name=wind.height.name,
            long_name="Height above sea level",
            units=wind.height.units,
            dimensions=wind.height.dimensions,
            data=wind.height.data + site_altitude,
        )

    wind.meridional_wind.plot(ax[0], wind.time, wind.height)
    model_meridional.plot(ax[1], mtime, mheight)

    wind.zonal_wind.plot(ax[2], wind.time, wind.height)
    model_zonal.plot(ax[3], mtime, mheight)

    wind.vertical_wind.plot(ax[4], wind.time, wind.height)

    wind.horizontal_wind_speed.plot(ax[5], wind.time, wind.height)
    mspeed.plot(ax[6], mtime, mheight)

    wind.horizontal_wind_direction.plot(ax[7], wind.time, wind.height)
    mdirec.plot(ax[8], mtime, mheight)

    writer.add_figure(f"wind-{args.site}_{args.date}", fig)


def _process_stare(args: argparse.Namespace) -> None:
    halo, halobg = get_halo_cloudnet(
        site=args.site, date=args.date, product=Product.STARE
    )
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


def _from_raw(args: argparse.Namespace) -> None:
    halo_src = [src for src in args.src if src.name.endswith(".hpl")]
    bg_src = [
        src
        for src in args.src
        if src.name.startswith("Background") and src.name.endswith(".txt")
    ]
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
    _print_raw_from_cloudnet_args(
        subparsers.add_parser(
            "print_raw_from_cloudnet", help="Prints raw files to stdout from cloudnet"
        )
    )

    return parser.parse_args()


def _from_cloudnet_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--site", type=str, default="warsaw")
    parser.add_argument(
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.date.today() - datetime.timedelta(days=1),
    )
    parser.add_argument(
        "--product", type=Product, default=Product.STARE, choices=list(Product)
    )


def _from_raw_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plot", action="store_true")
    parser.add_argument(
        "src",
        type=Path,
        nargs="*",
        default=[],
        help="Raw and background files in an arbitrary order",
    )
    parser.add_argument("-o", "--output", type=Path, required=True)


def _print_raw_from_cloudnet_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--site", type=str, default="warsaw")
    parser.add_argument(
        "--date",
        type=datetime.date.fromisoformat,
        default=datetime.date.today() - datetime.timedelta(days=1),
    )
    parser.add_argument("--nlines", type=int, default=16)
    parser.add_argument("--include-fname-regexp", type=str)
    parser.add_argument("--exclude-fname-regexp", type=str)
