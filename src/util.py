"""hr-saas-free-tier fetch/parse utilities."""
import re

import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
TIMEOUT = 18


def http_get(url: str, timeout: int = TIMEOUT) -> str | bytes | None:
    """Content best-effort; None 当页面不可达."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            return None
        return r.content
    except Exception:
        return None


def text_of(html) -> str:
    txt = html.decode("utf-8", "ignore") if isinstance(html, bytes) else html
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def host(url: str) -> str:
    import urllib.parse
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return url[:30]
