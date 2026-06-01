#!/usr/bin/env bash
# cmr-gate :: compute-diff-hash
#
# 算当前 staged 非文档文件的 diff_hash,和 harness_precommit_hook.py
# 内部算法**保证一致**(同样的排序、同样的 git diff 命令、同样的 sha256[0:16])。
#
# 用法:
#   bash scripts/cmr-gate/compute-diff-hash.sh
#
# 输出:diff_hash 一行(去掉换行,适合管道塞 frontmatter)。
# 没有 staged 非文档文件 → 输出空字符串 + exit 0。
#
# 为什么不让用户直接跑 `git diff --cached -- <files> | shasum`?
# 文件名含空格 / 引号 / 中文时,shell 引用规则容易翻车;且文件列表
# 必须和 hook 内部排序一致。这个脚本封装好。
set -e

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "[cmr-gate] not in a git repo" >&2
    exit 1
}
cd "$REPO_ROOT"

# 借用 hook 的 is_doc 逻辑(Python 化避免 bash 字符串处理坑)
python3 - <<'PY'
import hashlib
import os
import subprocess
import sys

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


raw = subprocess.check_output(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"]
)
files = [f.decode("utf-8", "replace") for f in raw.split(b"\0") if f]
non_doc = sorted(f for f in files if not is_doc(f))

if not non_doc:
    # 输出空 + 信号到 stderr
    print("[cmr-gate] no non-doc staged files (pure-doc commit needs no marker)",
          file=sys.stderr)
    print("")
    sys.exit(0)

diff = subprocess.check_output(["git", "diff", "--cached", "--"] + non_doc)
digest = hashlib.sha256(diff).hexdigest()[:16]
print(digest)
print(f"[cmr-gate] diff_hash={digest} over {len(non_doc)} file(s):",
      file=sys.stderr)
for f in non_doc[:8]:
    print(f"  - {f}", file=sys.stderr)
if len(non_doc) > 8:
    print(f"  ... 另 {len(non_doc) - 8} 个", file=sys.stderr)
PY
