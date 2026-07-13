# Cross-model review wiki upstream checklist

本文件由 issue #30 的 Step 2 压缩生成。下一个例行 sync PR 把下列逐字原文
纳入 wiki 后，勾选并删除本文件；不新建 `BACKENDS.md` 中间层。

## 待上游

- [ ] `cross-model-review.md` §降级链：补入 agy 的模型降级梯。被删叙事逐字原文：

```text
**agy model-degradation ladder** (the leg's own fallback): agy's
  Gemini quota is a small consumer Code Assist bucket that exhausts. When
  the preferred model **Gemini 3.5 Flash** quota-429s, `gemini.sh` steps
  the agy leg DOWN to **`Claude Sonnet 4.6 (Thinking)` via agy** — a
  SEPARATE quota bucket (verified), and deliberately a DIFFERENT model
  from the squad's Claude-Agent leg (Opus 4.8) for a distinct voice — so
  a third independent read survives. Only when EVERY rung is quota-
  exhausted does the agy leg step down entirely (degrade → `本轮缺
  gemini`). When a fallback rung runs, the round has **no Google voice**;
  `gemini.sh` flags that on stderr (the 3rd voice is then agy-served
  Claude, separate quota). `AGY_MODEL` env pins one explicit model
  (manual / tests). (Cross-family is the ideal, but Gemini is already
  quota-dead either way — a distinct same-family 3rd read beats only
  two; the wiki §降级链 should bless this rung.)
```
