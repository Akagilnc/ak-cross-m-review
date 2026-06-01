# cmr-gate — Cross-Model Review 真闸

防"agent 跑一轮 cmr 就停继续往下做"的两层闸。**L2 是真闸**(Claude Code
PreToolUse hook),**L1 是 audit 兜底**(post-commit log 留痕)。

## 为什么需要它

`vault/ak-cc-wiki/wiki/concepts/claude-code-hooks.md:177` 早就说明:

> 跳过 cross-model review、宣布假 DONE —— git-hook 治不全。review-skip
> 只有 harness-hook + gate marker 能绑,因为它要拦的是「动机性重框」,
> 那只能在 tool-call 层拦,不能在 commit-fact 层拦。

git pre-commit 只看「commit 时刻的事实」(报告文件存在 / mtime 新),挡不住:

- agent 跑 R1 → 拿 finding → 改 → 把 R1 report 和代码一起 commit(报告 mtime 新、文件名对)→ 跳过 R2 直接往下
- agent 自己用 `touch report.md` 伪造新鲜度

cmr-gate 在 **tool call 层** 拦,并把 marker 写入权和 agent 分离(verifier
script 才能写 marker,marker 由 report frontmatter 的 vendor verdicts
客观计算)。

## 两层架构

```
┌─────────────────────────────────────────────────────────────┐
│ L2 真闸  PreToolUse hook (harness, settings.local.json)      │
│          - 拦 Bash 工具调用 `git commit <非doc>`              │
│          - 要求 .cmr-gate/<diff_hash>.json concur=APPROVE     │
│          - marker 由 verifier 写,agent 不能直接写             │
├─────────────────────────────────────────────────────────────┤
│ L1 audit  post-commit (.githooks/post-commit)                │
│           - --no-verify / 外部 commit / hook 没装 时兜底       │
│           - 非文档 + 无/未收敛 report → .review-unconverged.log │
│           - 永不阻断,只留可 audit 痕迹                          │
└─────────────────────────────────────────────────────────────┘
```

## 装机

```bash
bash scripts/cmr-gate/install.sh
```

幂等。装机后:

> [!important] Bootstrap 提示:装它的 Claude Code session 内 L2 **不会**激活
> Claude Code 在 session 启动时读 `.claude/settings.local.json`。**当前 session 里
> 装的 hook 要等下次开 Claude Code session 才生效**。本 session 仍只有 L1 audit
> 兜底(post-commit 写日志,不阻断)。验 L2 真激活的方法:开新 session,故意
> stage 一个 .ts 文件然后 `git commit -m test`,看 hook 是否拦截。

- `.claude/settings.local.json` 含 PreToolUse Bash matcher → harness_precommit_hook.py
- `.githooks/post-commit` 可执行,通过 `package.json` postinstall 走的 `git config core.hooksPath .githooks` 已激活
- `.gitignore` 加 `.cmr-gate/` 和 `.review-unconverged.log`

## 使用流程

### 1. 跑 cross-model review,产 report

按 [[wiki/concepts/cross-model-review]] 协议跑 N+1+1。最终产物是一个
markdown report,frontmatter 必须严格如下:

```yaml
---
cmr_report: v1
round: 3
diff_hash: a1b2c3d4e5f60718   # 后面会教你怎么算
slice: auth-cookie-fix         # 切片名 or "ship-pre"
vendors:
  - name: claude
    verdict: APPROVE           # APPROVE | DEFER | OPEN
    findings: 0
  - name: codex
    verdict: APPROVE
    findings: 0
  - name: gemini
    verdict: APPROVE
    findings: 0
created: 2026-06-01T15:30:00+09:00
---

<review body markdown>
```

### 2. 算 diff_hash(必须和 hook 算的一致才能匹配 marker)

**推荐**:用 helper(封装好排序 + 是否 doc 判断,和 hook 内部算法 100% 一致):

```bash
bash scripts/cmr-gate/compute-diff-hash.sh
# → 输出一行 16 字符 hex,e.g. a1b2c3d4e5f60718
```

不推荐手算 `git diff | shasum`——文件名含空格/引号/中文时容易翻车,
且文件列表必须和 hook 同样的排序。

实操:在 staged 完代码后,跑 helper 得到 `diff_hash`,写进 report
frontmatter,**保证 report 之后到 commit 之间 staged 不变**(staged 一动
diff_hash 就变,marker 就对不上)。这是 marker-binding 的核心保证——见
`test_stage_change_invalidates_marker`。

### 3. 让 verifier 写 marker

```bash
python3 scripts/cmr-gate/verify_report.py path/to/report.md
```

成功输出:
```
[cmr-gate] ✓ report.md round 3 → concur=APPROVE → .cmr-gate/a1b2c3d4e5f60718.json
```

### 4. Commit

```bash
git commit -m "feat: ..."
```

如果 marker 存在 + concur=APPROVE + diff_hash 匹配 → 放行。否则 harness
hook 把这次 Bash 调用拦掉并告诉你缺什么。

## Concur 算法

- 任一 vendor `OPEN` → marker `OPEN`(拦)
- APPROVE 数 ≥ ceil(N × 2/3) → marker `APPROVE`(放行)
- 其它(主要是 DEFER 多)→ marker `DEFER`(拦,但可走 [[cross-model-review#修复(fix loop)]] 的 defer 协议)

阈值:N=2 全 APPROVE,N=3 ≥2 APPROVE,N=4 ≥3 APPROVE。

## 例外路径

### 纯文档 commit

只改 `.md / .mdx / .markdown / .txt / .rst / docs/...` → hook 直接放行,
无需 report。

### 真要绕过

```bash
git commit --no-verify -m "..."
```

L2 hook 接到 `--no-verify` 会主动放行(不强拦),但 L1 post-commit 会写一行
到 `.review-unconverged.log`:

```
2026-06-01T15:32:11+09:00  abc1234  NO_REPORT  files=3  author=Akagi  subj=...
```

便于事后 audit。

### Hook 自己挂了

**默认 fail-open**:hook 内部异常(import 错 / git 不可达 / OS 异常)→
stderr 警告 + exit 0(放行)。这避免 hook bug 把 agent 卡死。

要反开 fail-closed(hook 异常即拦,适合 CI / production-strict):

```bash
export CMR_GATE_STRICT=1
```

调试 traceback:

```bash
export CMR_GATE_DEBUG=1
```

### Hook 误伤(真有 bug)

可以临时把 `.claude/settings.local.json` 里 cmr-gate 那个 PreToolUse 条目
注释/删掉,或反装:

```bash
# 反装(等你确认要除掉)
python3 -c "
import json
from pathlib import Path
p = Path('.claude/settings.local.json')
d = json.loads(p.read_text())
d['hooks']['PreToolUse'] = [
    e for e in d['hooks'].get('PreToolUse', [])
    if not any('cmr-gate' in h.get('command', '') for h in e.get('hooks', []))
]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
"
```

## 设计权衡

### 为什么不重用 vela 的 `review-gate-precommit.sh`?

vela 那个是**git pre-commit**层(只看时刻事实),设计注释自己说明是「软痕迹」
不是真闸。cmr-gate 直接做 wiki 一直说"暂未建"的 harness-hook + gate marker
真闸,L1 是替代+扩展(扫 verdict 不只扫文件名)。

### 为什么 marker 在 `.cmr-gate/<diff_hash>.json` 而不是 commit 里?

- 让 marker 跟 diff 绑(stage 一变就失效),不让陈旧 marker 蒙混
- marker 不进 git history,不污染 commit
- per-machine,team 协作不互相干扰

### 为什么不让 agent 自己写 marker?

那就回到原点(cosplay APPROVE)。verifier 解析 report frontmatter 才能写
marker——agent 要伪造,得在 cmr 流程的多 vendor reviewer subagent 输出里
全部伪造 APPROVE。这一步在主 session 编排里需要 fabricate 多个
**子代理**的输出,且会在 conversation log 里留显眼痕迹(没真跑过 subagent 但
报告里却有它们的 verdict)。比 agent 直接 touch marker 难得多。

### 为什么 diff_hash 只取前 16 字节?

够避碰撞(2^64 量级),且短到 frontmatter 里好写、能记。

## 故障排查

| 症状 | 可能原因 | 处理 |
|---|---|---|
| `[cmr-gate] ✗ 无 gate marker` | 没跑 verify_report.py,或 staged 后又改了文件导致 diff_hash 变 | 跑 verify;或重新算 diff_hash 更新 report 后再跑 verify |
| `marker concur=OPEN/DEFER` | review 还没收敛 | 继续跑 cmr 下一轮,直到 ≥2/3 vendor APPROVE |
| hook 完全没触发(`git commit` 顺过) | `.claude/settings.local.json` 没装 PreToolUse,或 Claude Code 没读到这个 settings | 重跑 `install.sh`,确认 Claude Code 版本支持 PreToolUse hook |
| post-commit hook 没跑 | `git config core.hooksPath` 不是 `.githooks` | `npm install`(触发 postinstall 设 hooksPath),或手动 `git config core.hooksPath .githooks` |

## 关联

- 设计源 conversation: 2026-06-01 vault session,vault `wiki/concepts/claude-code-hooks.md`
- wiki 真闸定义:[[claude-code-hooks]]
- cmr 协议:[[cross-model-review]]
- 切片纪律:[[tdd-autonomous-dev]] §切片内纪律
