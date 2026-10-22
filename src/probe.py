"""链接体检：官方/第三方 URL 存活分类（🚫死链 / 🔒403需登录 / ✅存活）。"""
from src import util


def check(url: str) -> str:
    """返回状态标识：✅ / 🔒 / 🚫 / ⚠️。"""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": util.UA}, timeout=12, allow_redirects=True)
        if r.status_code == 200:
            return "✅"
        if r.status_code in (401, 403):
            return "🔒"
        if r.status_code in (404, 410):
            return "🚫"
        return "⚠️"
    except Exception:
        return "🚫"


def probe_vendor(v: dict) -> dict:
    """探测一家厂商的官方/第三方链接，返回状态映射。"""
    res = {"official": {}, "third": {}}
    for u in (v.get("official_sources") or []):
        res["official"][u] = check(u)
    for u in (v.get("third_party_sources") or []):
        res["third"][u] = check(u)
    return res
