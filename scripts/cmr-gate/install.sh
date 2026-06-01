#!/usr/bin/env bash
# cmr-gate :: installer (L1 audit only)
#
# L2(harness PreToolUse 真闸)已移除——复杂度收益不划算,bootstrap 麻烦,
# Claude Code session 加载语义模糊。改成单层 L1:post-commit 写
# .review-unconverged.log 留痕,永不阻断。看 .log 累积频次即知现状。
#
# 本 installer 做的事:
#   1. chmod .githooks/post-commit
#   2. 给 hooksPath 状态提示
#   3. .gitignore 加 .review-unconverged.log
#   4. 跑 postcommit_audit 自检
#
# 幂等。
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "==> cmr-gate L1 audit installer (idempotent)"
echo "  repo root: $REPO_ROOT"

# --- 1. post-commit hook chmod (鲁棒) ---
if [ -f .githooks/post-commit ]; then
  chmod +x .githooks/post-commit
  echo "  .githooks/post-commit +x"
else
  echo "  ⚠ .githooks/post-commit 不存在(跳过)"
fi

# --- 2. hooksPath 状态 ---
HP=$(git config core.hooksPath || echo "")
case "$HP" in
  .githooks)
    echo "  core.hooksPath = .githooks ✓"
    ;;
  "")
    echo "  ⚠ core.hooksPath 未设(默认 .git/hooks)。要让 .githooks/post-commit 生效:"
    echo "      git config core.hooksPath .githooks"
    ;;
  *)
    echo "  ⚠ core.hooksPath = $HP (不是 .githooks)。L1 audit 不会经 .githooks/post-commit 触发。"
    echo "    选项:"
    echo "      A) 切到 .githooks:git config core.hooksPath .githooks"
    echo "      B) chain cmr-gate L1 到现有 post-commit(见 README §既有 hook 共存)"
    ;;
esac

# --- 3. .gitignore (idempotent) ---
add_ignore() {
  local entry="$1"
  if ! grep -qxF "$entry" .gitignore 2>/dev/null; then
    echo "$entry" >> .gitignore
    echo "  .gitignore += $entry"
  fi
}
add_ignore ".review-unconverged.log"

# --- 4. 自检 ---
echo "==> postcommit_audit 自检"
python3 -c "import sys; sys.path.insert(0, 'scripts/cmr-gate'); import postcommit_audit; print('  ✓ import OK')"

echo ""
echo "==> 完成。下次非文档 commit 没带 cmr review 报告(.md 文件名含"
echo "    cross-model-review / *.cmr-review.md / *.review.md)时,post-commit 会写一行到"
echo "    .review-unconverged.log。永不阻断,只留痕。"
