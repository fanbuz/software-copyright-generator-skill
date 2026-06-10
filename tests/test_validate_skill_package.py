from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_skill_package.py"), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


class ValidateSkillPackageTests(unittest.TestCase):
    def test_validate_skill_package_outputs_json_and_passes(self) -> None:
        completed = run_validator("--json")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIs(payload["ok"], True)
        self.assertIs(payload["checks"]["frontmatter"]["ok"], True)
        self.assertIs(payload["checks"]["python_syntax"]["ok"], True)
        self.assertIs(payload["checks"]["sensitive_residue"]["ok"], True)

    def test_validate_skill_package_detects_missing_frontmatter(self) -> None:
        with self.subTest("missing description"):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as dirname:
                package = Path(dirname) / "bad-skill"
                package.mkdir()
                (package / "SKILL.md").write_text("---\nname: demo\n---\n# Demo\n", encoding="utf-8")
                (package / "README.md").write_text("# Demo\n", encoding="utf-8")
                (package / "agents").mkdir()
                (package / "agents/openai.yaml").write_text("name: demo\n", encoding="utf-8")
                (package / "scripts").mkdir()
                (package / "references").mkdir()

                completed = run_validator("--root", str(package), "--json")

                self.assertNotEqual(completed.returncode, 0)
                payload = json.loads(completed.stdout)
                self.assertIs(payload["ok"], False)
                self.assertIs(payload["checks"]["frontmatter"]["ok"], False)
                self.assertIn("description", "\n".join(payload["checks"]["frontmatter"]["errors"]))

    def test_validate_skill_package_detects_sensitive_residue(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            package = Path(dirname) / "leaky-skill"
            package.mkdir()
            (package / "SKILL.md").write_text(
                "---\nname: demo\n"
                "description: Use when testing demo skill packages.\n---\n# Demo\n",
                encoding="utf-8",
            )
            fake_token = "ghp_" + "A" * 36
            (package / "README.md").write_text(f"token = {fake_token}\n", encoding="utf-8")
            (package / "agents").mkdir()
            (package / "agents/openai.yaml").write_text("name: demo\n", encoding="utf-8")
            (package / "scripts").mkdir()
            (package / "references").mkdir()

            completed = run_validator("--root", str(package), "--json")

            self.assertNotEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["checks"]["sensitive_residue"]["ok"], False)
            self.assertTrue(any("GitHub token" in error for error in payload["checks"]["sensitive_residue"]["errors"]))


if __name__ == "__main__":
    unittest.main()
