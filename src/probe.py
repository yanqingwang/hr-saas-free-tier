"""链接体检：官方/第三方 URL 存活分类（🚫死链 / 🔒403需登录 / ✅存活），并行探测。"""
import concurrent.futures

import requests

from src import util


def _check(url: str, timeout: int = 8) -> str:
    """返回状态标识：✅ / 🔒 / 🚫 / ⚠️。"""
    try:
        r = requests.get(url, headers={"User-Agent": util.UA}, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return "✅"
        if r.status_code in (401, 403):
            return "🔒"
        if r.status_code in (404, 410):
            return "🚫"
        return "⚠️"
    except Exception:
        return "🚫"


def probe_vendor(v: dict, timeout: int = 8) -> dict:
    """探测一家厂商的官方/第三方链接（并行），返回状态映射。"""
    res = {"official": {}, "third": {}}
    jobs: list[tuple[str, str]] = []
    for u in (v.get("official_sources") or []):
        jobs.append(("official", u))
    for u in (v.get("third_party_sources") or []):
        jobs.append(("third", u))
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        fut = {u: ex.submit(_check, u, timeout) for _, u in jobs}
        for key, u in jobs:
            try:
                st = fut[u].result(timeout=timeout + 3)
            except Exception:
                st = "🚫"
            res[key][u] = st
    return res


def probe_all(vendors: list[dict], timeout: int = 8) -> dict:
    """全量厂商的所有 URL 一个线程池并行探测（避免厂商间串行拖时长）。"""
    # 汇总所有 URL
    all_jobs: list[tuple[str, str, str]] = []   # (vid, key, url)
    for v in vendors:
        for u in (v.get("official_sources") or []):
            all_jobs.append((v["id"], "official", u))
        for u in (v.get("third_party_sources") or []):
            all_jobs.append((v["id"], "third", u))
    out: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        fut = {u: ex.submit(_check, u, timeout) for _, _, u in all_jobs}
        for vid, key, u in all_jobs:
            try:
                st = fut[u].result(timeout=timeout + 3)
            except Exception:
                st = "🚫"
            out.setdefault(vid, {"official": {}, "third": {}})[key][u] = st
    return out
