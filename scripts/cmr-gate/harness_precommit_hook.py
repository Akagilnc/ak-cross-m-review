#!/usr/bin/env python3
"""
cmr-gate :: L2 真闸 = Claude Code PreToolUse harness hook

接 Claude Code PreToolUse hook 契约:
  stdin = JSON {"tool_name": "Bash", "tool_input": {"command": "..."}, ...}
  stdout/stderr 可见
  exit 0 = 放行, exit != 0 = 拦截(把 stderr 喂给 model)

本 hook **只在 Bash 工具调用是 `git commit` 时**生效。其它 tool call
一律放行。git commit 时:

  1. 解析 command → 是不是 git commit(不算 `git commit-tree` 之类)
  2. 含 --no-verify? → 放行(走 L1 post-commit audit 留痕)
  3. staged 全是 doc(.md/.mdx/docs/...)? → 放行
  4. 计算 diff_hash = sha256(git diff --cached -- <非 doc 文件>)[0:16]
  5. 读 .cmr-gate/<diff_hash>.json → concur == "APPROVE"? → 放行
  6. 否则 → 拦,告诉 agent 缺什么

不像 git pre-commit 那种 hook,本 hook 在 **tool call 前** 触发——
agent 的"我跑一轮就停"的动机性重框在这一层暴露:它必须先 cross-model
review 跑出 concur=APPROVE,verifier 才会写 marker,本 hook 才放行。
agent 自己不能写 marker(verify_report.py 才能写,而它解析 report
里的 vendor verdict,需要多 vendor 输出一致——伪造成本高)。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

DOC_EXT = {"md", "mdx", "markdown", "txt", "rst"}
DOC_DIR_PREFIXES = ("docs/",)
DOC_BASENAMES = {"LICENSE", "NOTICE", "CHANGELOG"}


def is_doc(path: str) -> bool:
    base = os.path.basename(path)
    if base in DOC_BASENAMES:
        return True
    if any(path.startswith(p) for p in DOC_DIR_PREFIXES):
        return True
    ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
    return ext in DOC_EXT


def detect_git_commit(command: str) -> tuple[bool, bool]:
    """
    返回 (is_git_commit, has_no_verify)。
    解析够鲁棒:
      - `git commit -m ...`、`git commit --amend` → True
      - `git commit-tree` → False
      - `git diff && git commit ...` → 仍触发(只要含 git commit token)
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        # 解析失败默认放行(避免 false positive 卡死 agent)
        return (False, False)
    is_commit = False
    no_verify = False
    i = 0
    while i < len(tokens):
        if tokens[i] == "git" and i + 1 < len(tokens):
            nxt = tokens[i + 1]
            if nxt == "commit":
                is_commit = True
                # 扫剩余 token 看 --no-verify
                for t in tokens[i + 2:]:
                    if t == "--no-verify" or t == "-n":
                        no_verify = True
                        break
                    # 遇到下一个 git 命令或 shell 分隔符就停
                    if t in ("&&", "||", ";", "|"):
                        break
                break
        i += 1
    return (is_commit, no_verify)


def staged_files(repo_root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "-C", str(repo_root), "diff", "--cached", "--name-only",
         "--diff-filter=ACM", "-z"]
    )
    files = [f.decode("utf-8", "replace") for f in out.split(b"\0") if f]
    # 排序保证 diff_hash 确定性(不依赖 git stage 顺序 / OS / git version)
    return sorted(files)


def compute_diff_hash(repo_root: Path, files: list[str]) -> str:
    """
    对 staged 非 doc 文件的 diff 内容算 sha256[0:16]。

    files 应已排序(由 staged_files 保证),确保:
      - hook 算的 hash = README 教用户算的 hash(`compute-diff-hash.sh` 同样排序)
      - 不同 stage 顺序、不同机器、不同 git version 算出来一致
    """
    if not files:
        return ""
    sorted_files = sorted(files)  # 防御性二次排序
    out = subprocess.check_output(
        ["git", "-C", str(repo_root), "diff", "--cached", "--"] + sorted_files
    )
    return hashlib.sha256(out).hexdigest()[:16]


def repo_root() -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def read_hook_input() -> dict:
    """读 stdin JSON。空 stdin → 空 dict(放行)。"""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    data = read_hook_input()
    if data.get("tool_name") != "Bash":
        return 0
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return 0

    is_commit, has_no_verify = detect_git_commit(command)
    if not is_commit:
        return 0

    if has_no_verify:
        # 放行 + 警告(post-commit audit 会留痕)
        print(
            "[cmr-gate] ⚠ --no-verify 检测到,放行但 post-commit audit 会记录到 "
            ".review-unconverged.log",
            file=sys.stderr,
        )
        return 0

    root = repo_root()
    if root is None:
        return 0  # 不在 git repo,不管

    files = staged_files(root)
    if not files:
        return 0  # 没 staged 内容,git commit 本身会失败,不是我们的事

    non_doc = [f for f in files if not is_doc(f)]
    if not non_doc:
        return 0  # 纯文档,放行

    # 关键:检查 gate marker
    diff_hash = compute_diff_hash(root, non_doc)
    marker_path = root / ".cmr-gate" / f"{diff_hash}.json"

    if not marker_path.exists():
        _block(
            non_doc, diff_hash,
            reason="无 gate marker——本次 diff 没跑 cross-model review,或 review 没收敛",
        )
        return 1

    try:
        marker = json.loads(marker_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        _block(non_doc, diff_hash, reason=f"marker 读取失败:{e}")
        return 1

    if marker.get("concur") != "APPROVE":
        _block(
            non_doc, diff_hash,
            reason=(
                f"marker concur={marker.get('concur')!r} ≠ APPROVE。"
                f"round={marker.get('round')} vendors={marker.get('vendor_verdicts')}"
            ),
        )
        return 1

    print(
        f"[cmr-gate] ✓ marker {diff_hash} concur=APPROVE round={marker['round']},放行",
        file=sys.stderr,
    )
    return 0


def _block(non_doc_files: list[str], diff_hash: str, reason: str) -> None:
    print("", file=sys.stderr)
    print("[cmr-gate] ✗ commit 被拦截(L2 真闸)", file=sys.stderr)
    print(f"  原因:{reason}", file=sys.stderr)
    print(f"  当前 diff_hash = {diff_hash}", file=sys.stderr)
    print(f"  非文档 staged 文件({len(non_doc_files)}):", file=sys.stderr)
    for f in non_doc_files[:8]:
        print(f"    - {f}", file=sys.stderr)
    if len(non_doc_files) > 8:
        print(f"    ... 另 {len(non_doc_files) - 8} 个", file=sys.stderr)
    print("", file=sys.stderr)
    print("  合规方式(任一):", file=sys.stderr)
    print(
        "    1. 跑 cross-model review 直到 concur=APPROVE,然后:",
        file=sys.stderr,
    )
    print(
        "       python3 scripts/cmr-gate/verify_report.py <report.md>",
        file=sys.stderr,
    )
    print(
        "       (report frontmatter 须含 diff_hash=" + diff_hash + ")",
        file=sys.stderr,
    )
    print(
        "    2. 真要紧急绕过:`git commit --no-verify`(会被 post-commit audit 留痕)",
        file=sys.stderr,
    )
    print("", file=sys.stderr)


def _main_safe() -> int:
    """
    Fail-open 兜底:如果 hook 自己挂了(import 错 / git 不可达 /
    OS 异常),不该 brick agent。打 stderr 警告然后放行。

    用 env CMR_GATE_STRICT=1 反开 fail-closed(hook 异常即拦),适合
    CI / production-strict 场景。
    """
    strict = os.environ.get("CMR_GATE_STRICT", "").strip() in ("1", "true", "TRUE")
    try:
        return main()
    except Exception as e:  # noqa: BLE001
        import traceback
        print(
            f"[cmr-gate] ⚠ hook 自己挂了({type(e).__name__}: {e}),"
            f"{'拦截(STRICT)' if strict else '放行(fail-open)'}",
            file=sys.stderr,
        )
        if os.environ.get("CMR_GATE_DEBUG"):
            traceback.print_exc(file=sys.stderr)
        return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(_main_safe())
