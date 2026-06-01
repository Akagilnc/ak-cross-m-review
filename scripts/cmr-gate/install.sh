#!/usr/bin/env bash
# cmr-gate :: installer
#
# 干两件事:
#   1. 把 PreToolUse hook 加进 .claude/settings.local.json (L2 真闸 wiring)
#      —— .claude/ 是 .gitignored,所以这一步是 per-machine
#   2. 把 .githooks/post-commit chmod +x (L1 audit)
#   3. 在 .gitignore 里加 .cmr-gate/ 和 .review-unconverged.log
#   4. 验装可用
#
# 重复跑安全(idempotent)。
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "==> cmr-gate installer (idempotent)"
echo "  repo root: $REPO_ROOT"

# --- 1. PreToolUse hook 写入 .claude/settings.local.json ---
SETTINGS=".claude/settings.local.json"
mkdir -p .claude
if [ ! -f "$SETTINGS" ]; then
  echo "{}" > "$SETTINGS"
  echo "  created empty $SETTINGS"
fi

python3 - "$SETTINGS" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
data = json.loads(settings_path.read_text() or "{}")
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# 检查是否已装 (按 command substring)
marker_str = "scripts/cmr-gate/harness_precommit_hook.py"
already = any(
    any(marker_str in h.get("command", "") for h in entry.get("hooks", []))
    for entry in pre
)
if already:
    print("  PreToolUse hook 已存在,跳过")
else:
    pre.append({
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": 'python3 "$CLAUDE_PROJECT_DIR/scripts/cmr-gate/harness_precommit_hook.py"',
                "timeout": 10,
                "statusMessage": "cmr-gate checking...",
            }
        ],
    })
    settings_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"  PreToolUse hook 装到 {settings_path}")
PY

# --- 2. post-commit hook chmod (鲁棒:文件不在不 abort) ---
if [ -f .githooks/post-commit ]; then
  chmod +x .githooks/post-commit
  echo "  .githooks/post-commit +x"
else
  echo "  ⚠ .githooks/post-commit 不存在(跳过 chmod)"
fi

# 也验 core.hooksPath 状态。不一致就 warn 不阻断
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
    echo "  ⚠ core.hooksPath = $HP (不是 .githooks)。L1 audit 经 .githooks/post-commit 不会触发。"
    echo "    选项:"
    echo "      A) 切到 .githooks:git config core.hooksPath .githooks"
    echo "      B) chain cmr-gate L1 到现有 post-commit(见 README §Vela-like 既有 hook)"
    ;;
esac

# --- 3. .gitignore 追加(idempotent) ---
add_ignore() {
  local entry="$1"
  if ! grep -qxF "$entry" .gitignore 2>/dev/null; then
    echo "$entry" >> .gitignore
    echo "  .gitignore += $entry"
  fi
}
add_ignore ".cmr-gate/"
add_ignore ".review-unconverged.log"

# --- 4. 跑 verifier 测试 ---
echo "==> verifier 自检"
if python3 scripts/cmr-gate/test_verify_report.py 2>&1 | tail -3; then
  echo "  ✓ verifier 测试通过"
else
  echo "  ✗ verifier 测试失败,装机失败"
  exit 1
fi

echo ""
echo "==> 完成。"
echo "下次 Claude Code 在本仓里跑 \`git commit\` 含非文档改动时,会先过 cmr-gate。"
echo "看 scripts/cmr-gate/README.md 了解协议。"
