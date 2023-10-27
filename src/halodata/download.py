import argparse
import logging
import re
from pathlib import Path

from halodata import exceptions
from halodata.api import Api

log = logging.getLogger(__name__)


def download(args: argparse.Namespace) -> None:
    if args.date is not None:
        date_params = {"date": args.date.isoformat()}
    elif args.date_from is not None and args.date_to is not None:
        date_params = {
            "dateFrom": args.date_from.isoformat(),
            "dateTo": args.date_to.isoformat(),
        }
    else:
        raise exceptions.CliArgumentError(
            "provide date OR (date-from AND date-to) arguments "
        )

    api = Api()
    records = api.get(
        "raw-files",
        params={
            **{
                "site": args.site,
                "instrument": "halo-doppler-lidar",
            },
            **date_params,
        },
    )

    records = _filter_records(args, records)

    records_sorted = sorted(
        records, key=lambda r: (r["measurementDate"], r["filename"])
    )
    for rec in records_sorted:
        log.info(
            "Downloading: %s from %s %s",
            rec["filename"],
            args.site,
            rec["measurementDate"],
        )
        tags = sorted(rec["tags"])
        tag_path = Path(*tags)
        bytes_io = api.get_record_content(rec)
        path = (
            args.dir / args.site / rec["measurementDate"] / tag_path / rec["filename"]
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(bytes_io.getbuffer())


def _filter_records(args: argparse.Namespace, records: list) -> list:
    records_out = []
    if isinstance(args.include, list) and len(args.include) > 0:
        records_filtered = []
        for r in records:
            if any(re.match(pattern, r["filename"]) for pattern in args.include):
                records_filtered.append(r)
        records_out += records_filtered
    else:
        records_out = records[:]

    if isinstance(args.exclude, list) and len(args.exclude) > 0:
        records_filtered = []
        for r in records_out:
            if not any(re.match(pattern, r["filename"]) for pattern in args.exclude):
                records_filtered.append(r)
        records_out = records_filtered
    return records_out
