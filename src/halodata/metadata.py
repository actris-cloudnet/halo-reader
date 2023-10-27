import argparse
import json
import logging
import sys
from datetime import date, datetime

import pandas as pd
from tabulate import tabulate

from halodata.api import Api
from halodata.database import Database

log = logging.getLogger(__name__)


def update_database(args: argparse.Namespace) -> None:
    db = Database()
    log.info("metadata main")
    api = Api()
    data_all = api.get(
        "raw-files",
        params={"instrument": "halo-doppler-lidar"},
        _no_cache=args.no_cache,
    )
    data = []
    keys = (
        "checksum",
        "createdAt",
        "downloadUrl",
        "filename",
        "instrumentId",
        "instrumentPid",
        "measurementDate",
        "siteId",
        "size",
        "status",
        "tags",
        "updatedAt",
        "uuid",
    )
    for record_all in data_all:
        record = {key: record_all.get(key) for key in keys}
        data.append(record)
    df = pd.DataFrame(data)

    def str2dt(s: str) -> datetime:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")

    def str2date(s: str) -> date:
        return datetime.strptime(s, "%Y-%m-%d").date()

    df["createdAt"] = df["createdAt"].apply(str2dt)
    df["updatedAt"] = df["updatedAt"].apply(str2dt)
    df["measurementDate"] = df["measurementDate"].apply(str2date)
    df["size"] = df["size"].apply(int)
    df.to_sql("raw", db.con, if_exists="replace", index=False, index_label="uuid")


def list_sites() -> None:
    db = Database()
    site = db.sites()
    json.dump(site, sys.stdout, indent=2)


def data_summary() -> None:
    db = Database()
    data = db.summary()
    sites_set = set(data.keys())
    years_set = set()
    for _, year_data in data.items():
        years_set.update(year_data.keys())

    years = sorted(list(years_set))
    sites = sorted(list(sites_set))
    table = []
    for site in sites:
        site_data = data.get(site, {})
        tsizes = [site_data.get(y) for y in years]
        tsizes = [s if s is not None else 0 for s in tsizes]
        tsizes = tsizes + [sum(tsizes)]
        tsizes = [sizeof_fmt(s) for s in tsizes]
        table.append([site] + tsizes)

    print(tabulate(table, ["site"] + years + ["total"]))


def sizeof_fmt(num: int | float, suffix: str = "B") -> str:
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
