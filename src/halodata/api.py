from __future__ import annotations

import hashlib
import io
import json
import logging
import pickle
from pathlib import Path
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from halodata import exceptions

log = logging.getLogger(__name__)

CACHE_PATH = Path("cache")


def cache(get: Callable) -> Callable:
    def func_wrap(api: Api, path: str, params: dict, _no_cache: bool = False) -> list:
        digest = hash_string(f"path\n{path}params\n{json.dumps(params)}")
        cache_path = CACHE_PATH / digest
        if cache_path.is_file() and not _no_cache:
            with cache_path.open("rb") as f:
                log.info("load from cache")
                data = pickle.load(f)
                if isinstance(data, list):
                    return data
                raise TypeError
        else:
            log.info("make request")
            data = get(api, path, params, _no_cache)
            CACHE_PATH.mkdir(exist_ok=True)
            with cache_path.open("wb") as f:
                log.info("write to cache")
                pickle.dump(data, f)
            if isinstance(data, list):
                return data
            raise TypeError

    return func_wrap


class Api:
    def __init__(self) -> None:
        retries = Retry(total=10, backoff_factor=0.2)
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session
        self.api_endpoint = "https://cloudnet.fmi.fi/api"

    @cache
    def get(self, path: str, params: dict, _no_cache: bool = False) -> list:
        res = self.session.get(
            f"{self.api_endpoint}/{path}", params=params, timeout=1800
        )
        if res.ok:
            data = res.json()
            if isinstance(data, list):
                return data
            raise exceptions.ApiRequestError(
                f"Unexpected response type from api: {type(data)}"
            )
        raise exceptions.ApiRequestError(f"Api request error: {res.status_code}")

    def get_record_content(self, rec: dict) -> io.BytesIO:
        res = self.session.get(rec["downloadUrl"])
        return io.BytesIO(res.content)


def hash_string(string: str) -> str:
    return hashlib.sha256(string.encode()).hexdigest()
