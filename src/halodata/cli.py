import argparse
import logging

from halodata import metadata

log = logging.getLogger(__name__)


def main() -> None:
    args, parser = _args()
    logging.basicConfig(level=args.log_level.upper())
    match args.subcmd:
        case "update-database":
            metadata.update_database(args)
        case "download-data":
            log.info("download-metadata")
        case "list-sites":
            metadata.list_sites()
        case "data-summary":
            metadata.data_summary()
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
    subparsers.add_parser("download-data")
    subparsers.add_parser("list-sites")
    subparsers.add_parser("data-summary")
    return parser.parse_args(), parser
