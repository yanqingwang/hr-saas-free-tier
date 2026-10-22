"""周报渲染：HR SaaS 免费版表格 + README 注入。"""
import datetime as dt


def _d(x) -> str:
    return x or "—"


def table(vendors: list[dict], probe_map: dict) -> str:
    """免费版总表（用户口径：免费版 / 免费情况 / 限制条件 / 何时需升级 / 最小付费包）。"""
    rows = [
        "| # | 公司 | 部署方式 | 模块说明 | 免费版 | 免费情况 | 限制条件 | 何时需升级 | 最小付费包 | 官方验证 | 第三方验证 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, v in enumerate(vendors, 1):
        conf = v.get("confidence") or "medium"
        badge = {"high": "", "medium": " <sub>☑️</sub>", "low": " <sub>⚠️</sub>"}.get(conf, " <sub>☑️</sub>")
        name = f"[{_d(v['name'])}]({_d(v['website'])}){badge}"
        deploy = v.get("deployment") or "—"
        modules = v.get("modules") or "—"
        free = v.get("free_plan") or "—"
        free_limits = v.get("free_limits") or "—"
        restrict = v.get("restrictions") or "—"
        trigger = v.get("upgrade_trigger") or "—"
        minpkg = v.get("min_paid_pkg") or "—"
        # 官方验证：列出每个官方 URL 的状态
        off = []
        for u, st in (probe_map.get(v["id"], {}).get("official") or {}).items():
            off.append(f"{st} [{util_host(u)}]({u})")
        third = []
        for u, st in (probe_map.get(v["id"], {}).get("third") or {}).items():
            third.append(f"{st} [{util_host(u)}]({u})")
        off_txt = "<br>".join(off) if off else "—"
        third_txt = "<br>".join(third) if third else "—"
        rows.append(
            f"| {i} | {name} | {deploy} | {modules} | {free} | {free_limits} | {restrict} | {trigger} | {minpkg} "
            f"| {off_txt} | {third_txt} |"
        )
    return "\n".join(rows)


def util_host(url: str) -> str:
    from src import util
    return util.host(url)


def report(vendors: list[dict], probe_map: dict, path: str) -> str:
    today = dt.date.today().isoformat()
    lines = [
        "# 中小人力资源 SaaS 免费版周报",
        "",
        f"**扫描周期：{today}（UTC）· 每周一自动更新**",
        "",
        "> 数据来自各厂商官方定价/免费版页面（每周探活核实），结论以官网为准；「无免费版」也如实列出。",
        "",
        "## 📊 HR SaaS 免费版总表",
        "",
        table(vendors, probe_map),
        "",
        "## 说明",
        "",
        "- 免费版：官方公开可用的免费层/免费试用/免费模块；试用到期或超人数即触发升级；",
        "- 最小付费包：该厂商最便宜的付费套餐（价格与内容）——「—」表示未公示；",
        "- 官方验证列：✅存活 / 🔒需登录或反爬 / 🚫死链，逐链接探活（每周自动）；",
        "- 数据核查置信：✅ 双源核实 / ☑️ 单源 / ⚠️ 待复核。",
        "",
        "## Roadmap",
        "",
        "- [ ] 补充更多国内中小 HR SaaS（2号人事部/薪人薪事/喔趣…）",
        "- [ ] 免费版人数上限自动提取（从定价页正文）",
        "- [ ] 邮件订阅（每周一自动送达，密文名单）",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def inject_readme(readme_path: str, vendors: list[dict], probe_map: dict) -> None:
    with open(readme_path, encoding="utf-8") as f:
        md = f.read()
    block = (
        "<!-- AUTO-TABLE-START -->\n"
        f"_每周一自动重建 · 数据定义于 [`data/vendors.yml`](data/vendors.yml) · 链接每周探活_\n\n"
        + table(vendors, probe_map)
        + "\n<!-- AUTO-TABLE-END -->"
    )
    start = md.index("<!-- AUTO-TABLE-START -->")
    end = md.index("<!-- AUTO-TABLE-END -->") + len("<!-- AUTO-TABLE-END -->")
    md = md[:start] + block + md[end:]
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(md)
