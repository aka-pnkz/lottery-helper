from __future__ import annotations

from functools import lru_cache
from typing import Final

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS: Final[dict[str, str]] = {
    "User-Agent": "Mozilla/5.0 (compatible; LotteryHelper/1.0)",
    "Accept": "*/*",
}

@lru_cache(maxsize=1)
def get_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(DEFAULT_HEADERS)
    return s
