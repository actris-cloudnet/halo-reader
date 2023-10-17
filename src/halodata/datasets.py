import datetime
import logging
import pathlib
from io import BytesIO

import requests
import urllib3

from haloreader.halo import Halo, HaloBg
from haloreader.read import read, read_bg
from haloreader.scantype import ScanType

log = logging.getLogger(__name__)


class Session(requests.Session):
    def __init__(self) -> None:
        super().__init__()
        retries = urllib3.util.retry.Retry(total=10, backoff_factor=0.2)
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.mount("https://", adapter)
        self.url = "https://cloudnet.fmi.fi/api/raw-files"

    def get_metadata(
        self, site: str, date_from: datetime.date, date_to: datetime.date
    ) -> list:
        records = self.get(
            self.url,
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


def get_halo_cloudnet(
    site: str, date: datetime.date, scantype: ScanType = ScanType.STARE
) -> tuple[Halo | None, HaloBg | None]:
    ses = Session()
    log.info("Fetching metadata for %s", date)
    records = ses.get_metadata(
        site, date_from=date - datetime.timedelta(days=30), date_to=date
    )
    bg_records = [r for r in records if HaloBg.is_bgfilename(r["filename"])]
    halo_records = [
        r
        for r in records
        if r["measurementDate"] == date.isoformat()
        and ScanType.from_filename(r["filename"]) == scantype
        and "cross" not in r.get("tags", [])
    ]
    halo_bytes = [_recor2bytes(r, ses) for r in halo_records]
    bg_bytes = [_recor2bytes(r, ses) for r in bg_records]
    bg_filenames = [r["filename"] for r in bg_records]
    return read(halo_bytes), read_bg(bg_bytes, bg_filenames)


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
