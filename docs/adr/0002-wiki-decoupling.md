# ADR 0002：Wiki 解耦

## Status

Accepted（2026-07-13）

## Context

本仓的 cmr 规则最初由
`~/WorkSpace/vault/ak-cc-wiki/wiki/concepts/cross-model-review.md`
转录而来，后续曾以 wiki 为单一事实源，并预期通过同步 PR 保持一致。
2026-07-13，用户裁定永久取消本仓与 wiki 之间的一切自动同步；两侧此后均可
独立演化和产生差异。既然同步停止，“wiki wins”已成为无法执行的死规则。

## Decision

1. 本环境的独立权威是 `SKILL.md` 与其 disclosed file `DOC-MODE.md` 的并集。
2. wiki 降为 lineage / 历史来源，不再决定本仓当前行为；“wiki wins”契约废止。
3. **RECORDED RULE / RECORDED divergence** 标记保留，但语义改为用户裁定账本：
   仅用户决定可更改，不得静默覆盖或删除。divergence 可继续记录相对 wiki
   历史来源的差异，但不表示等待同步。
4. `UPSTREAM-CHECKLIST.md` 未被消费即删除；不会再有同步 PR 消费该清单。

## Out of scope

- 不修改 wiki / vault 一侧。
- 不修改用户全局 `CLAUDE.md` 中指向 wiki flow 的规则。

## Consequences

- 对规则文档的修改在本仓内裁定，不再等待或追随 wiki 同步。
- 规则 provenance 由 prose 内 RECORDED 标记与 git 历史共同承担。
- ADR 0001 的同步耦合条款（Decision §3 上游化路径、Decision §5 wiki-wins
  与头部冻结约束、§Wiki sync 待办、Consequences 的 wiki
  同步者条）自此作废为历史记录；其余渐进披露边界（宿主差异不外置、①
  留主干、不得另建 BACKENDS.md、description 只留 identity+triggers）不变。
