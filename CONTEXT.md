# ak-cross-m-review 域上下文

## 域词表

- **lens**：一次 review 只采用的一套问题视角。完整性 lens 的权威是
  `prompts/cmr-completeness.md`；正确性 lens 的权威是
  `prompts/cmr-reviewer.md`。
- **完整性闸**：ship-pre Step 5，逐条判断 spec 是否交付；权威见 `SKILL.md`
  Step 0 与 `prompts/cmr-completeness.md`。
- **正确性闸**：ship-pre Step 6，在完整性通过后检查现有 diff 的缺陷；权威见
  `SKILL.md` Step 0 与 `prompts/cmr-reviewer.md`。两闸顺序执行，严禁合一。
- **宿主替换表**：把 main=Claude 主干映射到 main=Codex 的七行替换规则；权威是
  `SKILL.md` 的 `## main=Codex 宿主替换表`，不是独立运行规范。
- **disclosed file**：只在触发条件成立时由主干硬指针加载的规则文件。
  `DOC-MODE.md` 是该模式：设计文档 review 才披露 doc-mode ②–⑤。
- **RECORDED RULE / RECORDED divergence**：用户裁定账本；前者记录存续规则，
  后者可记录相对 wiki 历史来源的有意差异。仅用户可改；分类以 `SKILL.md`
  头部为权威。
- **契约级**：一个 reviewer leg 同时写清四要素：入口、硬禁令、降级旗、
  RECORDED marker（如适用）。权威实例见 `SKILL.md` Step 2。
- **待补守护**：已裁定但尚无可执行测试的行为叙事；在守护补齐前不得删除，
  权威见 `SKILL.md` Step 2 `### 待补守护（暂不得删）`。
- **缺钉闸**（仅限可执行代码面；ADR 0003 废止文档测试，prose 面无缺钉
  义务）：可执行面缺失必要测试/守护本身即 blocking finding；权威见
  `prompts/cmr-completeness.md` §缺钉闸。
- **交卷契约**：reviewer 对每条 finding 提交可核验、可裁定的完整论证；两个
  lens prompt 的 §Submission contract 各自为权威，有意重复。
- **step-down ≠ 降级**：agy 改用非 Google rung 仍是成功腿，但不再提供
  Google-family diversity，必须带 `NO Google voice this round`；权威见
  `SKILL.md` Step 2 Gemini bullet。
- **自查二连**：修复后检查 introduced regression 与同类遗漏；权威见
  `SKILL.md` Step 7。doc mode 由 `DOC-MODE.md` ⑤扩展为三连。
- **clear round**：所有存活腿均完成且达到当前 mode 的零 blocking finding
  条件的一轮；权威见 `SKILL.md` Step 5。
- **qualifying round / confirmation round**（仅 `CMR_DOUBLE_CLEAR=1` 开关
  开启时存在）：开关开启时第一轮 clear 只取得资格，下一轮必须 full
  re-review 再 clear 才收敛；**默认（开关关）单轮 clear 即收敛**
  （RECORDED 2026-07-14）。权威见 `SKILL.md` Step 5（终止信号）与
  Step 7（loop）；doc-mode 的
  ledger 口径见 `DOC-MODE.md` ②(c)。
- **能删大于能加**：同等功能优先删除机制而非增加机制；两个 lens prompt 的
  开头原则各自为权威，有意重复。
