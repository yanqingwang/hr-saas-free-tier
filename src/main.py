"""hr-saas-free-tier orchestrator.

用法:
    python -m src.main            # 探活 + 周报 + README 注入
    python -m src.main --mail     # 上同 + 邮件（需 SMTP secrets，预留）
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import yaml                                    # noqa: E402
from src import probe, render                  # noqa: E402


def load_vendors() -> list[dict]:
    with open(REPO_ROOT / "data" / "vendors.yml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("vendors") or []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mail", action="store_true", help="发送邮件（需 SMTP secrets）")
    args = ap.parse_args()

    vendors = load_vendors()
    probe_map = {}
    for v in vendors:
        try:
            probe_map[v["id"]] = probe.probe_vendor(v)
            print(f"[{v['id']}] {v['name']} probed", file=sys.stderr)
        except Exception as exc:
            print(f"[{v['id']}] probe error: {exc}", file=sys.stderr)

    # 周报
    rep_dir = REPO_ROOT / "reports"
    rep_dir.mkdir(exist_ok=True)
    render.report(vendors, probe_map, str(rep_dir / "weekly.md"))
    render.inject_readme(str(REPO_ROOT / "README.md"), vendors, probe_map)

    # 状态存档（供下轮 diff / 未来邮件）
    (REPO_ROOT / "data" / "probe-state.json").write_text(
        json.dumps(probe_map, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    if args.mail:
        try:
            from src import mailer
            body = (rep_dir / "weekly.md").read_text(encoding="utf-8")
            mailer.send(f"HR SaaS 免费版周报 {dt.date.today().isoformat()}", body,
                        str(rep_dir / "weekly.md"))
            print("邮件已发送（库主）", file=sys.stderr)
        except Exception as exc:
            print(f"邮件跳过: {type(exc).__name__}", file=sys.stderr)

    print(f"done: vendors={len(vendors)}", file=sys.stderr)


if __name__ == "__main__":
    main()
