import argparse
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from halodata import download, metadata

log = logging.getLogger(__name__)


def main() -> None:
    args, parser = _args()
    logging.basicConfig(level=args.log_level.upper())
    match args.subcmd:
        case "update-database":
            metadata.update_database(args)
        case "list-sites":
            metadata.list_sites()
        case "data-summary":
            metadata.data_summary()
        case "download":
            download.download(args)
        case _:
            parser.print_help()


def _args() -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default="info",
        choices=("error", "warning", "info", "debug"),
        help="Set log level",
    )
    subparsers = parser.add_subparsers(dest="subcmd")
    update_database = subparsers.add_parser("update-database")
    update_database.add_argument("--no-cache", action="store_true")
    subparsers.add_parser("list-sites")
    subparsers.add_parser("data-summary")
    download_data = subparsers.add_parser("download")
    download_data.add_argument("site", type=str)
    download_data.add_argument(
        "-d", "--date", type=_valid_date, help="Date in %Y-%m-%d format"
    )
    download_data.add_argument(
        "--date-from", type=_valid_date, help="Date in %Y-%m-%d format"
    )
    download_data.add_argument(
        "--date-to", type=_valid_date, help="Date in %Y-%m-%d format"
    )
    download_data.add_argument("--dir", type=Path, default=Path("data"))

    download_data.add_argument("--include", type=str, nargs="+", help="Regexp")
    download_data.add_argument("--exclude", type=str, nargs="+", help="Regexp")

    return parser.parse_args(), parser


def _valid_date(date_str: str) -> date:
    if date_str == "today":
        return date.today()
    if date_str == "yesterday":
        return date.today() - timedelta(days=1)

    format_ = "%Y-%m-%d"
    try:
        return datetime.strptime(date_str, format_).date()
    except ValueError as err:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str} , expecting format: {format_}"
        ) from err
