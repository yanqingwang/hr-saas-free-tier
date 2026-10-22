"""EN labels & boilerplate for the bilingual table/report.

Vendor-specific fact cells (免费情况/限制/升级/最小包) stay in Chinese with a
derived English "free-tier badge" (Free ≤N / Trial Nd / No free tier) so the
English table still answers "is there a free version?" without machine-translating
factual detail (translation could introduce errors).
"""

HEADERS_EN = {
    "#": "#", "company": "Company", "deploy": "Deploy", "modules": "Modules",
    "free": "Free tier", "free_limits": "Free terms", "restrictions": "Restrictions",
    "trigger": "Upgrade trigger", "minpkg": "Min paid plan",
    "official": "Official", "third": "3rd-party",
}

REPORT_EN = {
    "title": "Mid/Small HR SaaS Free-Tier Weekly · 中小人力资源 SaaS 免费版周报",
    "generated": "Scan date: {date} (UTC) · weekly auto-update every Monday",
    "note": "Facts verified weekly against official pricing/free pages; \"no free tier\" listed as-is. Detailed cells in Chinese (source facts); Free-tier badge is an English summary.",
    "h_en": "## 🌍 English — grouped by country",
    "h_zh": "## 中文（按国家分组）",
    "footer": "Links are probed weekly (✅ alive / 🔒 login-walled / 🚫 dead). Confidence: ✅ two-source / ☑️ single / ⚠️ unverified.",
}

CONF_EN = {"high": "", "medium": " <sub>☑️</sub>", "low": " <sub>⚠️</sub>"}

_FREE_PATTERNS = [
    (r"无免费版|无免费|无永久免费|无独立免费版", "No free tier"),
    (r"免费.*?(\d+)\s*(?:名|人|用户|员工|employees|users)", "Free ≤{n} {unit}"),
    (r"(\d+)\s*(?:名|人|用户|员工|employees|users).*?(?:免费|永久)", "Free ≤{n} {unit}"),
    (r"永久免费", "Free (permanent)"),
    (r"免费版", "Free tier"),
    (r"免费试用\s*(\d+)\s*(?:天|日|day)", "Free trial {n}d"),
    (r"试用\s*(\d+)\s*(?:天|日|day)", "Trial {n}d"),
    (r"(\d+)\s*天.*?免费试用", "Trial {n}d"),
    (r"免费试用|免费体验|无料トライアル", "Free trial"),
    (r"免费", "Free"),
]


def free_badge(free_plan: str) -> str:
    """从免费版描述提取英文短徽标（Free ≤N / Trial Nd / No free tier…）。"""
    t = free_plan or ""
    for pat, fmt in _FREE_PATTERNS:
        import re
        m = re.search(pat, t)
        if m:
            n = m.group(1) if m.lastindex else ""
            unit = "users"
            if "人" in t or "员工" in t:
                unit = "people"
            if "用户" in t:
                unit = "users"
            if "名员工" in t or "名用户" in t:
                unit = "employees" if "员工" in t else "users"
            # 兼容数字单位
            label = fmt.format(n=n, unit=unit) if m.lastindex else fmt
            return label
    return t if t and len(t) <= 24 else (t[:23] + "…" if t else "—")
