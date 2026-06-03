#!/usr/bin/env python3
"""
cmr-gate :: L1 audit = post-commit 留痕(防 L2 被绕过)

post-commit 不被 `git commit --no-verify` 跳过(那是 pre-commit 的事)。
本脚本作为 .githooks/post-commit 的内容,扫刚落地的 HEAD commit:

  - 含非文档? 否 → 静默放过
  - 含 cmr report .md (filename match cross-model-review|.cmr-review|.review)?
    - 是 → 解析 report frontmatter 看 vendors 全 APPROVE
    - 否 → 标记为「无 review 报告」
  - 任一异常 → 追加一行到 .review-unconverged.log

永不阻断,只留可 audit 的痕迹。

为什么不直接调 verify_report.py?那个写 marker,适合 pre-commit 决策;
本脚本只读 frontmatter 算 verdict,纯被动 audit,不污染 .cmr-gate/。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DOC_EXT = {"md", "mdx", "markdown", "txt", "rst"}
DOC_DIR_PREFIXES = ("docs/",)
DOC_BASENAMES = {"LICENSE", "NOTICE", "CHANGELOG"}
REVIEW_RE = re.compile(r"(cross-model-review|\.cmr-review|\.review)\.md$", re.I)


def is_doc(path: str) -> bool:
    base = os.path.basename(path)
    if base in DOC_BASENAMES:
        return True
    if any(path.startswith(p) for p in DOC_DIR_PREFIXES):
        return True
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
    return ext in DOC_EXT


def is_review_report(path: str) -> bool:
    return bool(REVIEW_RE.search(os.path.basename(path)))


def head_files(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "diff-tree", "--no-commit-id",
             "--name-only", "-r", "--diff-filter=ACM", "HEAD"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [l for l in out.split("\n") if l.strip()]


def head_meta(root: Path) -> dict:
    def g(arg: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), "log", "-1", arg, "HEAD"], text=True
        ).strip()
    return {
        "sha": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"], text=True
        ).strip(),
        "subj": g("--format=%s"),
        "author": g("--format=%an"),
    }


def parse_report_verdict(path: Path) -> tuple[str, dict]:
    """
    返回 (overall_verdict, parsed)。Overall:
      'APPROVE' / 'OPEN' / 'DEFER' / 'NO_FRONTMATTER' / 'PARSE_ERROR'
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ("PARSE_ERROR", {})
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        return ("NO_FRONTMATTER", {})
    body = m.group(1)
    verdicts: list[str] = []
    for line in body.split("\n"):
        m_v = re.match(r"^\s+verdict:\s*(\S+)\s*$", line)
        if m_v:
            verdicts.append(m_v.group(1))
    if not verdicts:
        return ("PARSE_ERROR", {})
    if "OPEN" in verdicts:
        return ("OPEN", {"verdicts": verdicts})
    n = len(verdicts)
    if verdicts.count("APPROVE") >= (n * 2 + 2) // 3:
        return ("APPROVE", {"verdicts": verdicts})
    return ("DEFER", {"verdicts": verdicts})


def main() -> int:
    try:
        root_str = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return 0
    root = Path(root_str)

    files = head_files(root)
    if not files:
        return 0
    non_doc = [f for f in files if not is_doc(f)]
    if not non_doc:
        return 0

    meta = head_meta(root)

    # 跳过自动化心跳 commits(blogger-style routine-fire publishing 每小时一条,
    # touch jsonl/audit 日志,不需要 cmr review,只会刷 audit log)。
    # 模式:subject 以 "chore: [routine]" 开头。env CMR_GATE_AUDIT_ALL=1 反开。
    if (not os.environ.get("CMR_GATE_AUDIT_ALL")
            and re.match(r"^chore: \[routine\]", meta["subj"])):
        return 0

    reports = [f for f in files if is_review_report(f)]
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    log_path = root / ".review-unconverged.log"

    def write_log(tag: str, detail: str) -> None:
        line = (
            f"{ts}  {meta['sha']}  {tag}  files={len(non_doc)}  "
            f"author={meta['author']}  subj={meta['subj'][:80]}  detail={detail}\n"
        )
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
        print(
            f"[cmr-gate] ⚠ {tag} → .review-unconverged.log "
            f"({meta['sha']} 含 {len(non_doc)} 非文档文件){' ' + detail if detail else ''}",
            file=sys.stderr,
        )

    if not reports:
        write_log("NO_REPORT", "")
        return 0

    # 多份 report 取最严的 verdict(OPEN > DEFER > PARSE_ERROR > APPROVE)
    severity = {"OPEN": 4, "DEFER": 3, "NO_FRONTMATTER": 2, "PARSE_ERROR": 2,
                "APPROVE": 0}
    worst = "APPROVE"
    worst_detail = ""
    for r in reports:
        v, info = parse_report_verdict(root / r)
        if severity.get(v, 0) > severity.get(worst, 0):
            worst = v
            worst_detail = f"report={r} verdicts={info.get('verdicts')}"

    if worst == "APPROVE":
        return 0  # 正常路径

    write_log(f"UNCONVERGED_{worst}", worst_detail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
