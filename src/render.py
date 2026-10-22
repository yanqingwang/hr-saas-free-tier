"""周报渲染：HR SaaS 免费版表格 + README 注入。"""
import datetime as dt


def _d(x) -> str:
    return x or "—"


def _region_group(region: str) -> tuple[str, str, int, str]:
    """region → (中文组名, 国旗, 排序权重, 英文组名)。"""
    r = (region or "").strip()
    base = r.split("（")[0].split("(")[0].strip()
    groups = [
        (("中国大陆",), "🇨🇳", 1, "China"),
        (("新加坡",), "🇸🇬", 2, "Singapore"),
        (("马来西亚",), "🇲🇾", 3, "Malaysia"),
        (("印尼",), "🇮🇩", 4, "Indonesia"),
        (("泰国",), "🇹🇭", 5, "Thailand"),
        (("日本",), "🇯🇵", 6, "Japan"),
        (("美国",), "🇺🇸", 7, "USA"),
        (("英国",), "🇬🇧", 8, "UK"),
        (("德国",), "🇩🇪", 9, "Germany"),
        (("西班牙",), "🇪🇸", 10, "Spain"),
        (("法国",), "🇫🇷", 11, "France"),
        (("荷兰",), "🇳🇱", 12, "Netherlands"),
        (("东欧",), "🇪🇺", 13, "Eastern Europe"),
        (("国际",), "🌍", 14, "International"),
    ]
    for keys, flag, order, en in groups:
        for k in keys:
            if k in base:
                return k, flag, order, en
    return (base or "其他"), "🗂️", 99, (base or "Other")


def table(vendors: list[dict], probe_map: dict, lang: str = "zh") -> str:
    """按国家/地区分组的免费版总表（每组子表，编号从 1 重计）；lang=en 时英文表头+免费档徽标。"""
    from src import i18n as I
    items = sorted(vendors, key=lambda v: (_region_group(v.get("region") or "")[2], v.get("name") or ""))
    sections: list[str] = []
    cur_group = None
    for v in items:
        label, flag, _, en_label = _region_group(v.get("region") or "")
        if label != cur_group:
            if sections:
                sections.append("")
            sections.append(f"#### {flag} {en_label if lang == 'en' else label}")
            hdr = I.HEADERS_EN if lang == "en" else None
            if hdr:
                sections.append(
                    "| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} | {8} | {9} | {10} |".format(
                        hdr["#"], hdr["company"], hdr["deploy"], hdr["modules"], hdr["free"],
                        hdr["free_limits"], hdr["restrictions"], hdr["trigger"], hdr["minpkg"],
                        hdr["official"], hdr["third"])
                )
            else:
                sections.append(
                    "| # | 公司 | 部署方式 | 模块说明 | 免费版 | 免费情况 | 限制条件 | 何时需升级 | 最小付费包 | 官方验证 | 第三方验证 |"
                )
            sections.append("|---|---|---|---|---|---|---|---|---|---|---|")
            cur_group = label
            no = 0
        no += 1
        conf = v.get("confidence") or "medium"
        badge = I.CONF_EN.get(conf, " <sub>☑️</sub>") if lang == "en" else {"high": "", "medium": " <sub>☑️</sub>", "low": " <sub>⚠️</sub>"}.get(conf, " <sub>☑️</sub>")
        name = f"[{_d(v['name'])}]({_d(v['website'])}){badge}"
        deploy = v.get("deployment") or "—"
        modules = v.get("modules") or "—"
        if lang == "en":
            fb = I.free_badge(v.get("free_plan") or "")
            free = f"**{fb}**<br><sub>{_d(v.get('free_plan'))}</sub>"
        else:
            free = v.get("free_plan") or "—"
        free_limits = v.get("free_limits") or "—"
        restrict = v.get("restrictions") or "—"
        trigger = v.get("upgrade_trigger") or "—"
        minpkg = v.get("min_paid_pkg") or "—"
        off = []
        for u, st in (probe_map.get(v["id"], {}).get("official") or {}).items():
            off.append(f"{st} [{util_host(u)}]({u})")
        third = []
        for u, st in (probe_map.get(v["id"], {}).get("third") or {}).items():
            third.append(f"{st} [{util_host(u)}]({u})")
        off_txt = "<br>".join(off) if off else "—"
        third_txt = "<br>".join(third) if third else "—"
        sections.append(
            f"| {no} | {name} | {deploy} | {modules} | {free} | {free_limits} | {restrict} | {trigger} | {minpkg} "
            f"| {off_txt} | {third_txt} |"
        )
    return "\n".join(sections)


def util_host(url: str) -> str:
    from src import util
    return util.host(url)


def report(vendors: list[dict], probe_map: dict, path: str) -> str:
    from src import i18n as I
    today = dt.date.today().isoformat()
    lines = [
        f"# {I.REPORT_EN['title']}",
        "",
        f"**{I.REPORT_EN['generated'].format(date=today)}**",
        "",
        f"> {I.REPORT_EN['note']}",
        "",
        I.REPORT_EN["h_en"],
        "",
        table(vendors, probe_map, lang="en"),
        "",
        I.REPORT_EN["h_zh"],
        "",
        table(vendors, probe_map, lang="zh"),
        "",
        "## 说明 / Notes",
        "",
        "- 免费版：官方公开可用的免费层/免费试用/免费模块；试用到期或超人数即触发升级；",
        "- 最小付费包：该厂商最便宜的付费套餐（价格与内容）——「—」表示未公示；",
        "- 官方验证列：✅存活 / 🔒需登录或反爬 / 🚫死链，逐链接探活（每周自动）；",
        "- 数据核查置信：✅ 双源核实 / ☑️ 单源 / ⚠️ 待复核；",
        "- Links probed weekly; detailed fact cells kept in Chinese to avoid translation drift.",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def inject_readme(readme_path: str, vendors: list[dict], probe_map: dict, lang: str = "zh") -> None:
    with open(readme_path, encoding="utf-8") as f:
        md = f.read()
    caption = {
        "zh": "每周一自动重建 · 数据定义于 [`data/vendors.yml`](data/vendors.yml) · 链接每周探活",
        "en": "auto-rebuilt weekly · source of truth in [`data/vendors.yml`](data/vendors.yml) · links probed weekly",
    }[lang]
    block = (
        "<!-- AUTO-TABLE-START -->\n"
        f"_{caption}_\n\n"
        + table(vendors, probe_map, lang=lang)
        + "\n<!-- AUTO-TABLE-END -->"
    )
    start = md.index("<!-- AUTO-TABLE-START -->")
    end = md.index("<!-- AUTO-TABLE-END -->") + len("<!-- AUTO-TABLE-END -->")
    md = md[:start] + block + md[end:]
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)
