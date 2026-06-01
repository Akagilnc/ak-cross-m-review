"""
cmr-gate verifier 单元测试。

不依赖 vitest(repo 的 TS 测试栈),用 stdlib unittest。运行:

    python3 -m unittest scripts/cmr-gate/test_verify_report.py
    # 或
    python3 scripts/cmr-gate/test_verify_report.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from verify_report import (  # noqa: E402
    ReportError,
    ReportUnreachable,
    compute_concur,
    main,
    parse_frontmatter,
    validate,
)


GOOD_REPORT = """---
cmr_report: v1
round: 3
diff_hash: a1b2c3d4e5f60718
slice: auth-cookie-fix
vendors:
  - name: claude
    verdict: APPROVE
    findings: 0
  - name: codex
    verdict: APPROVE
    findings: 0
  - name: gemini
    verdict: APPROVE
    findings: 0
created: 2026-06-01T15:30:00+09:00
---

# Review report body

R3 concur APPROVE.
"""


class FrontmatterParseTests(unittest.TestCase):
    def test_parses_good_report(self):
        d = parse_frontmatter(GOOD_REPORT)
        self.assertEqual(d["cmr_report"], "v1")
        self.assertEqual(d["round"], 3)
        self.assertEqual(d["diff_hash"], "a1b2c3d4e5f60718")
        self.assertEqual(d["slice"], "auth-cookie-fix")
        self.assertEqual(len(d["vendors"]), 3)
        self.assertEqual(d["vendors"][0],
                         {"name": "claude", "verdict": "APPROVE", "findings": 0})

    def test_rejects_no_frontmatter(self):
        with self.assertRaises(ReportUnreachable):
            parse_frontmatter("just a markdown file\nno frontmatter\n")

    def test_rejects_unclosed_frontmatter(self):
        with self.assertRaises(ReportUnreachable):
            parse_frontmatter("---\nround: 1\nno close")

    def test_handles_quoted_strings(self):
        text = """---
cmr_report: v1
round: 1
diff_hash: deadbeef
slice: "slice with: colon"
vendors:
  - name: claude
    verdict: APPROVE
    findings: 0
  - name: codex
    verdict: APPROVE
    findings: 0
created: 2026-06-01T00:00:00Z
---
body
"""
        d = parse_frontmatter(text)
        self.assertEqual(d["slice"], "slice with: colon")


class ValidateTests(unittest.TestCase):
    def _good(self) -> dict:
        return parse_frontmatter(GOOD_REPORT)

    def test_accepts_good(self):
        validate(self._good())  # no raise

    def test_rejects_missing_keys(self):
        d = self._good()
        del d["round"]
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_wrong_version(self):
        d = self._good()
        d["cmr_report"] = "v0"
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_zero_round(self):
        d = self._good()
        d["round"] = 0
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_bad_diff_hash(self):
        d = self._good()
        d["diff_hash"] = "not-hex!"
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_too_few_vendors(self):
        d = self._good()
        d["vendors"] = [d["vendors"][0]]
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_bad_verdict(self):
        d = self._good()
        d["vendors"][0]["verdict"] = "OK"
        with self.assertRaises(ReportError):
            validate(d)

    def test_rejects_negative_findings(self):
        d = self._good()
        d["vendors"][0]["findings"] = -1
        with self.assertRaises(ReportError):
            validate(d)


class ConcurTests(unittest.TestCase):
    def _v(self, *verdicts: str) -> list[dict]:
        return [
            {"name": f"v{i}", "verdict": v, "findings": 0}
            for i, v in enumerate(verdicts)
        ]

    def test_all_approve(self):
        self.assertEqual(compute_concur(self._v("APPROVE", "APPROVE", "APPROVE")),
                         "APPROVE")

    def test_any_open_blocks(self):
        # 即使 majority APPROVE,任一 OPEN 直接拦
        self.assertEqual(compute_concur(self._v("APPROVE", "APPROVE", "OPEN")),
                         "OPEN")

    def test_two_of_three_approve(self):
        # ceil(3*2/3) = 2 → 2/3 APPROVE 够
        self.assertEqual(compute_concur(self._v("APPROVE", "APPROVE", "DEFER")),
                         "APPROVE")

    def test_one_of_three_approve_defer(self):
        self.assertEqual(compute_concur(self._v("APPROVE", "DEFER", "DEFER")),
                         "DEFER")

    def test_two_vendors_both_approve(self):
        # ceil(2*2/3) = 2 → 必须全 APPROVE
        self.assertEqual(compute_concur(self._v("APPROVE", "APPROVE")), "APPROVE")

    def test_two_vendors_one_approve(self):
        self.assertEqual(compute_concur(self._v("APPROVE", "DEFER")), "DEFER")

    def test_four_vendors_threshold(self):
        # ceil(4*2/3) = 3 → 3/4 APPROVE 够
        self.assertEqual(
            compute_concur(self._v("APPROVE", "APPROVE", "APPROVE", "DEFER")),
            "APPROVE",
        )
        self.assertEqual(
            compute_concur(self._v("APPROVE", "APPROVE", "DEFER", "DEFER")),
            "DEFER",
        )


class EndToEndTests(unittest.TestCase):
    """跑一次 main() 看 marker 落盘对不对。需在 git repo 里。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"],
                       check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "t"],
                       check=True)
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def _write_report(self, text: str) -> Path:
        p = self.root / "report.md"
        p.write_text(text)
        return p

    def test_writes_approve_marker(self):
        report = self._write_report(GOOD_REPORT)
        rc = main(["verify_report.py", str(report)])
        self.assertEqual(rc, 0)
        marker = self.root / ".cmr-gate" / "a1b2c3d4e5f60718.json"
        self.assertTrue(marker.exists())
        m = json.loads(marker.read_text())
        self.assertEqual(m["concur"], "APPROVE")
        self.assertEqual(m["round"], 3)
        self.assertEqual(m["slice"], "auth-cookie-fix")
        self.assertEqual(m["vendor_verdicts"]["claude"], "APPROVE")

    def test_writes_open_marker_when_any_vendor_open(self):
        text = GOOD_REPORT.replace(
            "  - name: codex\n    verdict: APPROVE",
            "  - name: codex\n    verdict: OPEN",
        )
        # codex 那行的 findings 也得 > 0 不然不像真 OPEN——但 schema 允许 0
        report = self._write_report(text)
        rc = main(["verify_report.py", str(report)])
        self.assertEqual(rc, 0)  # marker 写成功,只是 concur 是 OPEN
        marker = self.root / ".cmr-gate" / "a1b2c3d4e5f60718.json"
        m = json.loads(marker.read_text())
        self.assertEqual(m["concur"], "OPEN")

    def test_rejects_schema_violation(self):
        report = self._write_report("---\ncmr_report: v0\n---\nbody")
        rc = main(["verify_report.py", str(report)])
        self.assertEqual(rc, 1)
        self.assertFalse((self.root / ".cmr-gate").exists())

    def test_rejects_missing_file(self):
        rc = main(["verify_report.py", str(self.root / "nope.md")])
        self.assertEqual(rc, 2)

    def test_rejects_no_frontmatter(self):
        report = self._write_report("# just markdown\n")
        rc = main(["verify_report.py", str(report)])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
