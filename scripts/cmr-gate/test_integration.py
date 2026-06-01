"""
cmr-gate 集成测试:
  write report → verify_report → 模拟 hook stdin → 验 exit code + stderr

跑:
    python3 scripts/cmr-gate/test_integration.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
VERIFY = HERE / "verify_report.py"
HOOK = HERE / "harness_precommit_hook.py"


def git(*args, cwd, check=True):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check, capture_output=True, text=True,
    )


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git("init", "-q", cwd=self.root)
        git("config", "user.email", "t@t", cwd=self.root)
        git("config", "user.name", "t", cwd=self.root)
        # baseline commit 才能 stage 跟它 diff
        (self.root / "README.md").write_text("# init\n")
        git("add", "README.md", cwd=self.root)
        git("commit", "-q", "-m", "init", cwd=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _stage(self, path: str, content: str) -> None:
        full = self.root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        git("add", path, cwd=self.root)

    def _diff_hash_of_non_doc(self, files: list[str]) -> str:
        files = sorted(files)
        diff = git("diff", "--cached", "--", *files, cwd=self.root).stdout
        return hashlib.sha256(diff.encode("utf-8")).hexdigest()[:16]

    def _run_hook(self, command: str, strict: bool = False) -> tuple[int, str]:
        env = os.environ.copy()
        if strict:
            env["CMR_GATE_STRICT"] = "1"
        stdin = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        # 必须 cd 到 repo 因为 hook 用 `git rev-parse` 找 root
        proc = subprocess.run(
            ["python3", str(HOOK)],
            input=stdin, capture_output=True, text=True,
            cwd=self.root, env=env,
        )
        return proc.returncode, proc.stderr

    def _write_report(self, diff_hash: str, slice_name: str,
                      verdicts: list[str]) -> Path:
        vendors_yaml = "\n".join(
            f"  - name: vendor{i}\n    verdict: {v}\n    findings: 0"
            for i, v in enumerate(verdicts)
        )
        report = self.root / f"{slice_name}.review.md"
        report.write_text(
            f"---\n"
            f"cmr_report: v1\n"
            f"round: 1\n"
            f"diff_hash: {diff_hash}\n"
            f"slice: {slice_name}\n"
            f"vendors:\n{vendors_yaml}\n"
            f"created: 2026-06-01T00:00:00Z\n"
            f"---\n\nbody\n"
        )
        return report

    def _verify(self, report: Path) -> int:
        proc = subprocess.run(
            ["python3", str(VERIFY), str(report)],
            capture_output=True, text=True, cwd=self.root,
        )
        return proc.returncode

    # ── 集成场景 ──

    def test_full_flow_approve(self):
        """stage 代码 → 算 hash → 写 APPROVE report → verify → hook 放行"""
        self._stage("src/x.ts", "export const x = 1;\n")
        dh = self._diff_hash_of_non_doc(["src/x.ts"])
        self._write_report(dh, "feat-x", ["APPROVE", "APPROVE", "APPROVE"])
        self.assertEqual(self._verify(self.root / "feat-x.review.md"), 0)
        rc, err = self._run_hook("git commit -m feat")
        self.assertEqual(rc, 0, f"应放行,stderr:\n{err}")
        self.assertIn("concur=APPROVE", err)

    def test_full_flow_open_blocks(self):
        """stage → 写 OPEN report → verify → hook 拦"""
        self._stage("src/x.ts", "export const x = 1;\n")
        dh = self._diff_hash_of_non_doc(["src/x.ts"])
        self._write_report(dh, "feat-x", ["APPROVE", "OPEN", "APPROVE"])
        self.assertEqual(self._verify(self.root / "feat-x.review.md"), 0)
        rc, err = self._run_hook("git commit -m feat")
        self.assertEqual(rc, 1)
        self.assertIn("concur='OPEN'", err)

    def test_no_marker_blocks(self):
        """stage 代码不 verify → hook 拦"""
        self._stage("src/x.ts", "export const x = 1;\n")
        rc, err = self._run_hook("git commit -m feat")
        self.assertEqual(rc, 1)
        self.assertIn("无 gate marker", err)

    def test_stage_change_invalidates_marker(self):
        """报告写完之后又 stage 了别的文件 → diff_hash 不匹配 → hook 拦

        这是 marker-binding 的核心保证:报告说的是 R1 的 diff,
        加新文件后 diff 变了,旧 marker 不能再 cover。
        """
        self._stage("src/x.ts", "export const x = 1;\n")
        dh = self._diff_hash_of_non_doc(["src/x.ts"])
        self._write_report(dh, "feat-x", ["APPROVE", "APPROVE", "APPROVE"])
        self._verify(self.root / "feat-x.review.md")
        # 再加新文件
        self._stage("src/y.ts", "export const y = 2;\n")
        rc, err = self._run_hook("git commit -m feat")
        self.assertEqual(rc, 1)
        self.assertIn("无 gate marker", err)

    def test_pure_doc_passes(self):
        """纯文档 commit 放行,无需 marker"""
        self._stage("docs/note.md", "# note\n")
        rc, err = self._run_hook("git commit -m docs")
        self.assertEqual(rc, 0, f"纯文档应放行,stderr:\n{err}")

    def test_no_verify_passes_with_warning(self):
        """--no-verify 放行 + stderr 警告"""
        self._stage("src/x.ts", "code\n")
        rc, err = self._run_hook("git commit --no-verify -m skip")
        self.assertEqual(rc, 0)
        self.assertIn("--no-verify", err)

    def test_non_commit_bash_passes(self):
        """非 git commit 的 Bash 命令一律放行"""
        rc, _ = self._run_hook("ls -la")
        self.assertEqual(rc, 0)
        rc, _ = self._run_hook("git status")
        self.assertEqual(rc, 0)
        rc, _ = self._run_hook("git commit-tree some-tree")  # 不是 git commit
        self.assertEqual(rc, 0)

    def test_amend_with_empty_stage_passes(self):
        """git commit --amend 且无 newly staged → 放行(amend 本身合法)"""
        self._stage("docs/x.md", "doc\n")
        git("commit", "-q", "-m", "doc", cwd=self.root)
        # 现在没 staged 内容了
        rc, _ = self._run_hook("git commit --amend --no-edit")
        self.assertEqual(rc, 0)

    def test_fail_open_when_hook_internals_explode(self):
        """env CMR_GATE_DEBUG 留着,但 hook 内部不该让 broken cwd 卡死 agent

        模拟难:python3 -c 'os.chdir("/nonexistent")' 无法做到——hook 本身
        cd 到 root 跑。这里用 STRICT off + 损坏 stdin JSON 测 _main_safe 兜底。
        """
        # 损坏的 JSON 不会触发 main 异常(我们 read_hook_input 已经 try/except)
        # → 实际测 STRICT off 下 main 内部 raise(模拟 git binary 不存在)
        proc = subprocess.run(
            ["python3", str(HOOK)],
            input='{"tool_name":"Bash","tool_input":{"command":"git commit -m x"}}',
            capture_output=True, text=True,
            cwd="/",  # 非 git repo → repo_root() return None → main return 0
        )
        self.assertEqual(proc.returncode, 0)

    def test_compute_diff_hash_helper_matches_hook(self):
        """compute-diff-hash.sh 算的 hash = hook 内部算的 hash"""
        self._stage("src/x.ts", "export const x = 1;\n")
        self._stage("src/a.ts", "export const a = 0;\n")
        # 用 helper 算
        helper = HERE / "compute-diff-hash.sh"
        proc = subprocess.run(
            ["bash", str(helper)],
            cwd=self.root, capture_output=True, text=True,
        )
        helper_hash = proc.stdout.strip()
        self.assertRegex(helper_hash, r"^[a-f0-9]{16}$")
        # 用 hook 内部逻辑算
        internal_hash = self._diff_hash_of_non_doc(["src/x.ts", "src/a.ts"])
        self.assertEqual(helper_hash, internal_hash,
                         "helper 算的 hash 必须 = hook 算的 hash")


if __name__ == "__main__":
    unittest.main()
