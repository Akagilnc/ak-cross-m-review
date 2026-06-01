#!/usr/bin/env python3
"""
cmr-gate :: verifier (L2 真闸的不可伪造层)

读 cross-model-review report 的 YAML frontmatter,验 schema,算 concur,
写 gate marker 到 .cmr-gate/<diff_hash>.json。

**关键**:本脚本是 agent **不能**直接调用 marker 写入的中介——agent
能写 report.md(prose),但 marker 是这个脚本根据 report 内 vendor
verdicts 客观计算的。agent 想伪造 APPROVE 必须改足够多 vendor 行的
verdict,这一步在 cmr 流程里需要 fabricate reviewer 子代理输出——
比直接写 marker 难得多,且会在 cross-model review 的多 vendor 输出
里留下显眼痕迹。

## Report frontmatter schema (v1)

    ---
    cmr_report: v1
    round: <int>           # 当前 review 轮次
    diff_hash: <str>       # `git diff` over non-doc staged 的 sha256 前16位
    slice: <str>           # 切片名 或 "ship-pre"
    vendors:               # 至少 2 个 vendor
      - name: claude
        verdict: APPROVE   # APPROVE | DEFER | OPEN
        findings: 0
      - name: codex
        verdict: APPROVE
        findings: 0
      - name: gemini
        verdict: APPROVE
        findings: 0
    created: 2026-06-01T15:30:00+09:00
    ---
    <markdown body>

## Concur 规则

- 任一 vendor OPEN → concur=OPEN(拦)
- 所有非 OPEN 中 APPROVE >= ceil(N*2/3) → concur=APPROVE(放行)
- 其它(主要是 DEFER 多)→ concur=DEFER(拦,但可走 defer 协议)

## Marker schema (写到 .cmr-gate/<diff_hash>.json)

    {
      "diff_hash": "...",
      "concur": "APPROVE",
      "round": 3,
      "slice": "auth-cookie-fix",
      "verified_at": "ISO-8601",
      "report_path": "path/to/report.md",
      "vendor_verdicts": {"claude": "APPROVE", ...}
    }

## Exit codes

  0  marker 写成功(concur 任意值,marker 里反映)
  1  report schema 违例 / 缺字段 / vendor 不够
  2  report 文件读不到 / 无 frontmatter
  3  filesystem error 写不进 marker

"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_TOP_KEYS = {"cmr_report", "round", "diff_hash", "slice", "vendors", "created"}
VALID_VERDICTS = {"APPROVE", "DEFER", "OPEN"}
MIN_VENDORS = 2


class ReportError(Exception):
    """Schema / parse 错误,exit 1。"""


class ReportUnreachable(Exception):
    """文件 / frontmatter 读不到,exit 2。"""


def parse_frontmatter(text: str) -> dict:
    """
    最小 YAML frontmatter 解析器(只处理本 schema 用到的形状)。
    避免引入 pyyaml 依赖。schema 是固定的,不需要通用 YAML。

    支持:scalar(int/str)、嵌套 list-of-dict(vendors)、ISO timestamp。
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        raise ReportUnreachable("no frontmatter delimiter (---) found at start")
    body = m.group(1)

    data: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        # top-level key: value
        m_kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m_kv:
            raise ReportError(f"unparseable line: {line!r}")
        key, val = m_kv.group(1), m_kv.group(2).strip()

        if val == "":
            # nested block (list of dicts or dict)
            if key == "vendors":
                vendors, consumed = _parse_vendors_block(lines, i + 1)
                data["vendors"] = vendors
                i += 1 + consumed
                continue
            else:
                # unknown nested key → skip but record empty
                data[key] = None
                i += 1
                continue

        # scalar value
        data[key] = _coerce_scalar(val)
        i += 1

    return data


def _coerce_scalar(val: str):
    """str→int/str (no quotes-handling needed for our fixed schema)。"""
    val = val.strip()
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if re.match(r"^-?\d+$", val):
        return int(val)
    return val


def _parse_vendors_block(lines: list[str], start: int) -> tuple[list[dict], int]:
    """
    解析:
        vendors:
          - name: claude
            verdict: APPROVE
            findings: 0
          - name: codex
            ...
    返回 (list[dict], consumed_line_count)。
    """
    vendors: list[dict] = []
    current: dict | None = None
    consumed = 0
    for line in lines[start:]:
        # 顶层 key 出现(无前导空格,有冒号)→ vendors block 结束
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:", line):
            break
        consumed += 1
        if not line.strip():
            continue
        # 新 vendor entry: "  - name: claude"
        m_new = re.match(r"^\s*-\s*name:\s*(.+)$", line)
        if m_new:
            if current is not None:
                vendors.append(current)
            current = {"name": m_new.group(1).strip()}
            continue
        # vendor field: "    verdict: APPROVE"
        m_f = re.match(r"^\s+([A-Za-z_]+):\s*(.+)$", line)
        if m_f and current is not None:
            current[m_f.group(1)] = _coerce_scalar(m_f.group(2).strip())
            continue
        # 其它非空 → 异常
        raise ReportError(f"unparseable vendors line: {line!r}")
    if current is not None:
        vendors.append(current)
    return vendors, consumed


def validate(data: dict) -> None:
    missing = REQUIRED_TOP_KEYS - set(data.keys())
    if missing:
        raise ReportError(f"missing required keys: {sorted(missing)}")
    if data.get("cmr_report") != "v1":
        raise ReportError(f"cmr_report must be 'v1', got {data.get('cmr_report')!r}")
    if not isinstance(data.get("round"), int) or data["round"] < 1:
        raise ReportError(f"round must be positive int, got {data.get('round')!r}")
    diff_hash = data.get("diff_hash")
    if not isinstance(diff_hash, str) or not re.match(r"^[a-f0-9]{8,64}$", diff_hash):
        raise ReportError(f"diff_hash must be hex 8-64 chars, got {diff_hash!r}")
    if not isinstance(data.get("slice"), str) or not data["slice"]:
        raise ReportError("slice must be non-empty str")
    vendors = data.get("vendors")
    if not isinstance(vendors, list) or len(vendors) < MIN_VENDORS:
        raise ReportError(f"vendors must be list of >= {MIN_VENDORS}")
    for v in vendors:
        if not isinstance(v, dict):
            raise ReportError(f"vendor entry must be dict, got {v!r}")
        for k in ("name", "verdict", "findings"):
            if k not in v:
                raise ReportError(f"vendor missing key {k!r}: {v!r}")
        if v["verdict"] not in VALID_VERDICTS:
            raise ReportError(
                f"vendor {v['name']!r} verdict must be in {sorted(VALID_VERDICTS)}, "
                f"got {v['verdict']!r}"
            )
        if not isinstance(v["findings"], int) or v["findings"] < 0:
            raise ReportError(f"vendor {v['name']!r} findings must be non-negative int")


def compute_concur(vendors: list[dict]) -> str:
    """
    任一 OPEN → OPEN
    APPROVE >= ceil(N*2/3) → APPROVE
    其它 → DEFER
    """
    verdicts = [v["verdict"] for v in vendors]
    if "OPEN" in verdicts:
        return "OPEN"
    n = len(verdicts)
    approve_threshold = (n * 2 + 2) // 3  # ceil(n*2/3)
    if verdicts.count("APPROVE") >= approve_threshold:
        return "APPROVE"
    return "DEFER"


def write_marker(
    repo_root: Path, data: dict, report_path: Path, concur: str
) -> Path:
    marker_dir = repo_root / ".cmr-gate"
    marker_dir.mkdir(exist_ok=True)
    marker_path = marker_dir / f"{data['diff_hash']}.json"
    payload = {
        "diff_hash": data["diff_hash"],
        "concur": concur,
        "round": data["round"],
        "slice": data["slice"],
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "report_path": str(report_path.relative_to(repo_root))
        if report_path.is_absolute()
        else str(report_path),
        "vendor_verdicts": {v["name"]: v["verdict"] for v in data["vendors"]},
    }
    marker_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return marker_path


def repo_root_from(path: Path) -> Path:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path.parent if path.is_file() else path),
             "rev-parse", "--show-toplevel"],
            text=True,
        ).strip()
        return Path(out)
    except subprocess.CalledProcessError as e:
        raise ReportError(f"not in a git repo: {e}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify_report.py <report.md>", file=sys.stderr)
        return 1
    report_path = Path(argv[1])
    if not report_path.exists():
        print(f"[cmr-gate] report not found: {report_path}", file=sys.stderr)
        return 2
    try:
        text = report_path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[cmr-gate] read failed: {e}", file=sys.stderr)
        return 2
    try:
        data = parse_frontmatter(text)
    except ReportUnreachable as e:
        print(f"[cmr-gate] {e}", file=sys.stderr)
        return 2
    try:
        validate(data)
    except ReportError as e:
        print(f"[cmr-gate] schema error: {e}", file=sys.stderr)
        return 1

    concur = compute_concur(data["vendors"])
    try:
        root = repo_root_from(report_path.resolve())
        marker = write_marker(root, data, report_path.resolve(), concur)
    except (OSError, ReportError) as e:
        print(f"[cmr-gate] marker write failed: {e}", file=sys.stderr)
        return 3
    print(
        f"[cmr-gate] ✓ {report_path.name} round {data['round']} → "
        f"concur={concur} → {marker.relative_to(root)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
