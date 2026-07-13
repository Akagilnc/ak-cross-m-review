# ADR 0003：机制需要事故基础；文档的账本是 git，不是 pytest

## Status

Accepted（2026-07-13）

## Context

2026-07-13 的架构审查（issue #35）把六个「深化候选」送进 grilling，
其中四个的正确答案是删除被深化对象本身。共同病根：防御 / 审计 / 冻结
机制在没有事故、没有生产者、没有读者的情况下按"以防万一"逐条累积，
never 走正常设计流程。实例：

- cmr-gate L1 audit（#37）：verdict 解析分支零 producer，审计 log
  64/64 全 NO_REPORT，零判别力——为不存在的报告格式维护 168 行。
- 文档一致性测试（#38）：98 个测试函数冻结 prose 措辞。in-repo 测试
  拦不住有测试写权限的 worker（撞红会去改测试；solo 仓 CODEOWNERS
  因作者不可自批而结构性失效）；裁定账本本就活在 prose 的 RECORDED
  标记与 git 史里（`git log -S` 可考古）。
- 降级 JSON 哨兵（#39，W3 落地）：outage 路径三条冗余通道，零个消费端读第三条。

本仓是 skill，不是系统：错误便宜、可修、git 可考古。

## Decision

1. **文档测试永久废止。** 不得添加任何 doc-pin、golden hash、措辞
   冻结、frontmatter 结构断言类测试。规则留痕 = prose 内 RECORDED
   标记 + commit message + git 史。
2. **新增防御 / 审计 / 校验机制必须先答两问：事故在哪？消费端在哪？**
   任一缺失 → 不得引入。既有机制经同问任一不过 → 删除。
3. **代码行为测试不受影响。** backend subprocess 行为测试与
   `codex-review.sh --selftest` 存续——它们测可执行代码、有真实事故史
   （D1/D2 调用形式四轮回归），按 TDD 继续。
4. **selftest 类调用形式自查是合法机制，存废看事故基础。**
   codex 侧存续（四次真实翻车）；gemini/agy 侧为「暂不需要」的
   deferral，**非永久禁止**——agy 侧出现真实调用形式事故即为重开依据。

## Consequences

- 未来 architecture review / 新 session 不得把 doc-pin 测试、audit
  hook、对称 selftest 类项目当"改进"重新提案（2026-07-13 审查中两个
  被标 Strong 的候选正是此类，均被 grilling 推翻）。
- 提案新机制的模板问题固定为：「哪次事故？谁在读？」
- 测试套件缩为行为层（39 个行为用例 + selftest），TESTING.md 的两层模型
  自此成为对套件的真实描述（#38）。
