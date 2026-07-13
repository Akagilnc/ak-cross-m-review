# ADR 0001：渐进披露 skill 正文

## Status

Accepted（2026-07-13）

## Context

`SKILL.md` 同时承担入口、运行契约和长篇 doc-mode 纪律，导致默认上下文过重，
也让同一规则容易在 description、宿主说明、测试文档和 prompt 间形成多个事实源。
本次拆分必须减载，但不能改变 runner、lens 或宿主行为。

已落地的拆分以实际边界为准：doc-mode ②–⑤ 移至 `DOC-MODE.md`；①
constitution packet + kill-axis 因适用于所有 review mode，留在 `SKILL.md`。
Step 0 对设计文档提供硬指针。mainline 仍按 main=Claude 书写；main=Codex 的七行
替换表留在 `SKILL.md`。Step 2 的调用形式按契约级保留，并把唯一待考古项放入
`UPSTREAM-CHECKLIST.md`。三个 skill description 只保留 identity + triggers。

## Decision

### 拆分红线

1. 宿主差异不外置。`SKILL.md` 是可直接执行的 main=Claude 主干；
   `## main=Codex 宿主替换表` 只替换宿主相关行，不另建宿主文件。
2. ① constitution packet + kill-axis 留在主干；只披露 doc-mode ②–⑤。
   ① 的 residual pointer 与 Step 0 硬指针共同指向 `DOC-MODE.md`。
3. 考古内容上游化：待同步的 wiki 原文进入 `UPSTREAM-CHECKLIST.md`，不得另建
   `BACKENDS.md` 作为第二层规则源。
4. description 只表达 skill identity + triggers；运行规则及例外不得复制进去。
5. `SKILL.md` 头部保持原样；现有 wiki-wins / RECORDED 契约不新增说明。

### Golden-hash 迁移规则

拆分本身产生两个 freeze boundary：`SKILL.md` residual text hash 与
`DOC-MODE.md` whole-file hash（completeness-lens addendum 的既有 golden hash
独立于本次拆分，不在此列）。迁移必须在同一个 commit 中原子完成：先让测试同时
识别旧权威与新披露文件，再在同一变更中切换两条 hash 及双向
anti-dual-source/shared-rationale-survival 断言。不得先删旧 hash 或先落无保护的新文件；
任一中间提交都不能出现规则无 freeze boundary 的真空期。

### 规则 → 唯一权威位置映射

| 规则 | 唯一权威位置 | 允许存在的 pointer / 重复位置 |
|---|---|---|
| per-slice 无 Claude | `SKILL.md` Step 1 `setup: who runs it decides the squad + the N table` / §谁跑 | description 层以 absence guard 维持缺席（测试禁止机制词回流），非正向指针；main=Codex 宿主替换表 |
| Fable 禁用 | `SKILL.md` Step 2 Claude bullet 的 `RECORDED RULE（存续）— Fable 禁用` | `SKILL.md` Step 1/3 提及 |
| «严禁合一次 cmr 闸» | `SKILL.md` Step 0 completeness / correctness 两条 | `CONTEXT.md` 域词表 |
| codex effort default + override | `SKILL.md` Step 2 `Reasoning-effort contract` | `TESTING.md`、`README.md` 仅作操作 pointer |
| 缺钉闸 | `prompts/cmr-completeness.md` §缺钉闸 | `CONTEXT.md` 域词表 |
| 交卷契约 | 两个 lens prompt 的 §Submission contract | 两处有意重复，分别约束各 lens |
| 能删大于能加 | 两个 lens prompt 的开头原则 | 两处有意重复，分别约束各 lens |
| doc-mode ②–⑤ | `DOC-MODE.md` | `SKILL.md` Step 0 硬指针 + ① residual pointer |
| step-down ≠ 降级 | `SKILL.md` Step 2 Gemini bullet | `CONTEXT.md` 域词表 |

映射表是后续 dedup 轮（审计 #2 余项）的基准。pointer 只能指向权威，不得重述
足以独立执行的规则；上表标为“有意重复”的两个 lens 契约除外。

### Wiki sync 待办

下一个例行 wiki sync PR 在 wiki 侧补一行 skill 布局注记：转写面由
`SKILL.md` 与 disclosed file `DOC-MODE.md` 共同组成。本片只记录待办，不改 wiki。

## Consequences

- 默认加载面缩小，doc-mode 调用者通过 Step 0 才披露 ②–⑤；① 不会因拆分失去
  code-diff 适用性。
- 宿主替换、调用硬禁令和降级语义仍在执行主干中，可被一次读取完整获得。
- 拆分产生的两条 hash 与反双源断言形成无真空期保护；新增 ADR、CONTEXT 和 CLAUDE 映射
  只做存在性/关键句测试，不进入 golden hash。
- wiki 同步者必须把 `SKILL.md` + `DOC-MODE.md` 视为转写并集，并依映射表去重。
