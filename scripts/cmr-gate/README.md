# cmr-gate — Cross-Model Review L1 audit

**只是 post-commit 留痕,不阻断**。非文档 commit 没带 cmr review 报告时,
追加一行到 `.review-unconverged.log`。看 log 累积频次即知现状。

## 历史

原本有 L2 真闸(Claude Code PreToolUse harness hook)做硬拦截,但实操踩了:

- Hook 必须在 session 启动时载入,装机 → 重启 session 这套 bootstrap 麻烦
- `$CLAUDE_PROJECT_DIR` 在不同上下文行为不一致
- session 必须 rooted 在仓库根才能加载该仓 settings,`cd <other-repo>` 后 Bash 调用不触发当仓 hook

收益不抵复杂度。**已移除**。等有更好的机制(e.g. project-agnostic harness hook,
或 sub-agent 强制注入)再上。

## 装机

```bash
bash scripts/cmr-gate/install.sh
```

幂等。

## 触发逻辑

`.githooks/post-commit` 调 `postcommit_audit.py`:

1. HEAD commit 含非文档(`.md` / `.mdx` / `docs/` / `LICENSE` / `NOTICE` / `CHANGELOG` 以外)? 否 → 静默放过
2. commit 含 review 报告 `.md`(名匹配 `cross-model-review` / `*.cmr-review.md` / `*.review.md`)?
   - 否 → 写 `.review-unconverged.log` 标 `NO_REPORT`
   - 是 → 解析 frontmatter,vendor verdicts 全 APPROVE? 否 → 写 log 标 `UNCONVERGED_<OPEN|DEFER|PARSE_ERROR>`
3. 永不阻断

## Report frontmatter (可选)

`postcommit_audit.py` 解析以下形状(没有也 OK,只会标 `NO_FRONTMATTER`):

```yaml
---
vendors:
  - name: claude
    verdict: APPROVE   # APPROVE | DEFER | OPEN
  - name: codex
    verdict: APPROVE
---
```

Concur 规则:任一 `OPEN` → log;APPROVE 数 < ceil(N×2/3) → log。

## 既有 hook 共存

如果本仓 `core.hooksPath` 不是 `.githooks/`(e.g. vela 用 `.git/hooks/` 绝对路径,
`.git/hooks/post-commit` 已被本地 review-gate 占用),`.githooks/post-commit`
不会自动触发。chain 到既有 post-commit 末尾:

```bash
cat >> .git/hooks/post-commit <<'CHAIN'

# ── cmr-gate L1 audit (chained) ──
_CMR_HOOK="$(git rev-parse --show-toplevel)/scripts/cmr-gate/postcommit_audit.py"
[ -f "$_CMR_HOOK" ] && python3 "$_CMR_HOOK" || true
CHAIN
```

幂等性自检:`grep -q "cmr-gate/postcommit_audit.py" .git/hooks/post-commit`

## .review-unconverged.log 格式

```
2026-06-01T15:32:11+09:00  abc1234  NO_REPORT  files=3  author=Akagi  subj=...
```

或:

```
2026-06-01T15:35:22+09:00  def5678  UNCONVERGED_OPEN  files=2  author=Akagi  subj=...  detail=report=x.review.md verdicts=['APPROVE', 'OPEN']
```

便于事后 audit。`--no-verify` 不能跳过 post-commit,所以这个 log 抓得到绕过。

## 关联 wiki

- [[claude-code-hooks]] § 177 —— 真闸只能在 tool-call 层(为什么 git-pre-commit 不够,以及为什么 L2 没坚持)
- [[cross-model-review]] —— Report 协议 + concur 规则
