import datetime
import logging
import pathlib
from io import BytesIO

import netCDF4
import requests
import urllib3

from haloreader.halo import Halo, HaloBg
from haloreader.read import read, read_bg
from haloreader.scangroup import ScanGroup
from haloreader.scantype import ScanType

log = logging.getLogger(__name__)


class Session(requests.Session):
    def __init__(self) -> None:
        super().__init__()
        retries = urllib3.util.retry.Retry(total=10, backoff_factor=0.2)
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.mount("https://", adapter)
        self.url_raw = "https://cloudnet.fmi.fi/api/raw-files"
        self.url_model = "https://cloudnet.fmi.fi/api/model-files"
        self.url_sites = "https://cloudnet.fmi.fi/api/sites"

    def get_sites_metadata(self) -> list:
        records = self.get(self.url_sites).json()
        if not isinstance(records, list):
            raise TypeError
        return records

    def get_metadata(
        self, site: str, date_from: datetime.date, date_to: datetime.date
    ) -> list:
        records = self.get(
            self.url_raw,
            params={
                "instrument": "halo-doppler-lidar",
                "site": site,
                "dateFrom": str(date_from),
                "dateTo": str(date_to),
            },
        ).json()
        if not isinstance(records, list):
            raise TypeError
        return records

    def get_metadata_models(self, site: str, date: datetime.date) -> list:
        records = self.get(
            self.url_model, params={"site": site, "date": str(date)}
        ).json()
        if not isinstance(records, list):
            raise TypeError
        return records


def get_halo_cloudnet(
    site: str, date: datetime.date, scangroup: ScanGroup = ScanGroup.STARE
) -> tuple[Halo | None, HaloBg | None]:
    ses = Session()
    log.info("Fetching metadata for %s", date)
    records = ses.get_metadata(
        site, date_from=date - datetime.timedelta(days=30), date_to=date
    )
    bg_records = [
        r
        for r in records
        if HaloBg.is_bgfilename(r["filename"]) and "cross" not in set(r["tags"])
    ]
    halo_records = [
        r
        for r in records
        if r["measurementDate"] == date.isoformat()
        and Halo.is_hplfilename(r["filename"])
        and "cross" not in set(r["tags"])
    ]
    if scangroup == ScanGroup.STARE:
        halo_bytes = [
            _recor2bytes(r, ses)
            for r in halo_records
            if ScanType.from_filename(r["filename"]) == ScanType.STARE
        ]
    else:
        halo_bytes = [
            _recor2bytes(r, ses)
            for r in halo_records
            if ScanType.from_filename(r["filename"]) != ScanType.STARE
        ]
        halo_bytes = [b for b in halo_bytes if _filter_by_scan_group(b, scangroup)]

    bg_bytes = [_recor2bytes(r, ses) for r in bg_records]
    bg_filenames = [r["filename"] for r in bg_records]
    return read(halo_bytes), read_bg(bg_bytes, bg_filenames)


def _filter_by_scan_group(raw_io: BytesIO, scangroup: ScanGroup) -> bool:
    halo = read([raw_io])
    raw_io.seek(0)
    return scangroup == ScanGroup.from_halo(halo)


def _recor2bytes(record: dict, session: Session) -> BytesIO:
    path = pathlib.Path("cache", record["uuid"])
    if path.exists():
        with path.open("rb") as f:
            file_io = BytesIO(f.read())
    else:
        log.info("Downloading and caching %s", record["filename"])
        file_bytes = session.get(record["downloadUrl"]).content
        path.parent.mkdir(exist_ok=True)
        with path.open("wb") as f:
            f.write(file_bytes)
        file_io = BytesIO(file_bytes)
    return file_io


def get_model_cloudnet(site: str, date: datetime.date) -> netCDF4.Dataset | None:
    ses = Session()
    records = ses.get_metadata_models(site, date)
    if len(records) == 0:
        return None
    if len(records) > 1:
        raise NotImplementedError
    _bytes = _recor2bytes(records[0], ses)
    return netCDF4.Dataset("inmemory.nc", memory=_bytes.read())


def get_site_cloudnet(site: str) -> dict:
    ses = Session()
    records = ses.get_sites_metadata()
    record, *_ = [r for r in records if r.get("id") == site]
    if isinstance(record, dict):
        return record
    raise TypeError
