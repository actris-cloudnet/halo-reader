import logging
import pathlib
from collections import defaultdict
from typing import Callable, Iterable

import requests
import urllib3

from haloreader.halo import HaloBg
from haloreader.read import read, read_bg
from haloreader.scantype import ScanType


class Session(requests.Session):
    def __init__(self) -> None:
        super().__init__()
        retries = urllib3.util.retry.Retry(total=10, backoff_factor=0.2)
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.mount("https://", adapter)
        self.url = "https://cloudnet.fmi.fi/api/raw-files"

    def get_records(
        self,
        site: str,
        date_from: str,
        date_to: str,
        scantype: ScanType,
    ) -> tuple[list[dict], list[dict]]:
        if date_to is None:
            date_to = date_from
        records = self.get(
            self.url,
            params={
                "instrument": "halo-doppler-lidar",
                "site": site,
                "dateFrom": date_from,
                "dateTo": date_to,
            },
        ).json()
        records_halo = []
        records_bg = []
        for rec in records:
            if ScanType.from_filename(rec["filename"]) == scantype:
                records_halo.append(rec)
            elif HaloBg.is_bgfilename(rec["filename"]):
                records_bg.append(rec)
        return records_halo, records_bg

    def get_background_records(
        self, site: str, date_from: str, date_to: str
    ) -> list[dict]:
        records = self.get(
            self.url,
            params={
                "instrument": "halo-doppler-lidar",
                "site": site,
                "dateFrom": date_from,
                "dateTo": date_to,
            },
        ).json()
        records_bg = []
        for rec in records:
            if HaloBg.is_bgfilename(rec["filename"]):
                records_bg.append(rec)
        return records_bg


def _keyfun(key: str) -> Callable[[dict], str]:
    def _fun(record: dict) -> str:
        val = record[key]
        if isinstance(val, str):
            return val
        raise TypeError

    return _fun


class CloudnetDataset:
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        root: str,
        site: str,
        scantype: str,
        date_from: str,
        date_to: str,
    ):
        self.root = root
        self.session = Session()
        records_halo, records_bg = self.session.get_records(
            site=site,
            date_from=date_from,
            date_to=date_to,
            scantype=ScanType[scantype.upper()],
        )
        self.records_halo = _group_by(
            records_halo, "measurementDate", sort_group_by="filename"
        )
        self.records_bg = _group_by(
            records_bg, "measurementDate", sort_group_by="filename"
        )

    def __iter__(self) -> Iterable:
        dates = sorted(
            set(list(self.records_halo.keys()) + list(self.records_bg.keys()))
        )
        for date in dates:
            records_halo = self.records_halo.get(date, None)
            file_paths_halo = (
                [_get_file(self.root, self.session, r) for r in records_halo]
                if records_halo is not None
                else []
            )
            records_bg = self.records_bg.get(date, None)
            file_paths_bg = (
                [_get_file(self.root, self.session, r) for r in records_bg]
                if records_bg is not None
                else []
            )
            yield date, read(file_paths_halo), read_bg(file_paths_bg)


class CloudnetBackgroundDataset:
    def __init__(
        self,
        root: str,
        site: str,
        date_from: str,
        date_to: str,
    ):
        self.root = root
        self.session = Session()
        records_bg = self.session.get_background_records(
            site=site,
            date_from=date_from,
            date_to=date_to,
        )
        self.records_bg = _group_by(
            records_bg, "measurementDate", sort_group_by="filename"
        )

    def __iter__(self) -> Iterable:
        for date, records in sorted(self.records_bg.items()):
            file_paths_bg = [
                _get_file(self.root, self.session, r) for r in records
            ]
            yield date, read_bg(file_paths_bg)


def _get_file(root: str, session: Session, record: dict) -> pathlib.Path:
    trg_path = _record2path(root, record)
    if trg_path.exists():
        if not trg_path.is_file():
            raise FileNotFoundError(f"{trg_path} is not a file")
        return trg_path
    logging.info("Downloading %s", trg_path)
    res = session.get(record["downloadUrl"])
    trg_path.parent.mkdir(parents=True, exist_ok=True)
    with trg_path.open("wb") as f:
        f.write(res.content)
    return trg_path


def _record2path(root: str, record: dict) -> pathlib.Path:
    return pathlib.Path(
        root, record["siteId"], record["measurementDate"], record["filename"]
    )


def _group_by(
    records: list[dict], key: str, sort_group_by: str | None = None
) -> dict:
    groups = defaultdict(list)
    for rec in records:
        groups[rec[key]].append(rec)
    if sort_group_by is not None:
        for k, recs in groups.items():
            groups[k] = sorted(recs, key=_keyfun(sort_group_by))
    return groups
