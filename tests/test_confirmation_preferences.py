from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def make_confirmable_workdir(base: Path, pending_application_field: bool = True) -> Path:
    """Build a workdir where drafts exist and only the confirmation actions are missing."""
    workdir = base / "work"
    draft = workdir / "草稿"
    draft.mkdir(parents=True)
    (draft / "业务理解.json").write_text(json.dumps({"user_confirmed": False}, ensure_ascii=False), encoding="utf-8")
    (draft / "代码文件选择.json").write_text(
        json.dumps(
            {
                "selection_required": True,
                "model_selection_required": True,
                "user_confirmed": False,
                "files": [
                    {"path": "src/main.ts", "selected": True, "model_reason": "入口文件，体现启动逻辑。"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    field_value = "待用户确认" if pending_application_field else "演示公司"
    (draft / "申请表信息.md").write_text(
        "\n".join(["# 申请表信息", "", "➤软件全称：演示任务管理系统", "➤版本号：V1.0", f"➤著作权人：{field_value}"]) + "\n",
        encoding="utf-8",
    )
    return workdir


class ConfirmationPreferencesTests(unittest.TestCase):
    def test_set_mode_record_and_show_roundtrip(self) -> None:
        with TemporaryDirectory() as dirname:
            workdir = Path(dirname) / "work"

            completed = run_script(
                "confirmation_preferences.py",
                "--workdir",
                str(workdir),
                "--set-mode",
                "auto",
                "--note",
                "用户选择默认直走",
                "--record",
                "screenshot_method=skip",
                "--record",
                "template_mode=default",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["confirmation_mode"], "auto")
            self.assertEqual(payload["choices"]["screenshot_method"], "skip")
            self.assertEqual(payload["choices"]["template_mode"], "default")

            shown = run_script("confirmation_preferences.py", "--workdir", str(workdir), "--show")
            self.assertEqual(shown.returncode, 0)
            self.assertEqual(json.loads(shown.stdout)["choices"]["screenshot_method"], "skip")

    def test_apply_defaults_requires_auto_mode(self) -> None:
        with TemporaryDirectory() as dirname:
            workdir = Path(dirname) / "work"

            completed = run_script("confirmation_preferences.py", "--workdir", str(workdir), "--apply-defaults")

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("STOP_FOR_USER", completed.stdout + completed.stderr)
            self.assertIn("--set-mode auto", completed.stdout + completed.stderr)

    def test_apply_defaults_confirms_choice_gates_and_reports_data_gates(self) -> None:
        with TemporaryDirectory() as dirname:
            workdir = make_confirmable_workdir(Path(dirname), pending_application_field=True)
            run_script("confirmation_preferences.py", "--workdir", str(workdir), "--set-mode", "auto")

            completed = run_script("confirmation_preferences.py", "--workdir", str(workdir), "--apply-defaults")

            self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
            report = json.loads(completed.stdout)
            self.assertIn("environment", report["auto_confirmed"])
            self.assertIn("screenshot-method(skip)", report["auto_confirmed"])
            self.assertIn("business", report["auto_confirmed"])
            self.assertIn("code-selection", report["auto_confirmed"])
            pending_stages = {item["stage"] for item in report["pending"]}
            self.assertIn("application-fields", pending_stages)
            self.assertIn("markdown", pending_stages)
            method = json.loads((workdir / "截图方式确认.json").read_text(encoding="utf-8"))
            self.assertEqual(method["screenshot_method"], "skip")

    def test_apply_defaults_full_pass_when_data_complete(self) -> None:
        with TemporaryDirectory() as dirname:
            workdir = make_confirmable_workdir(Path(dirname), pending_application_field=False)
            run_script("confirmation_preferences.py", "--workdir", str(workdir), "--set-mode", "auto")

            completed = run_script("confirmation_preferences.py", "--workdir", str(workdir), "--apply-defaults")

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["pending"], [])
            self.assertIn("markdown", report["auto_confirmed"])

    def test_confirm_stage_records_screenshot_method_preference(self) -> None:
        with TemporaryDirectory() as dirname:
            workdir = Path(dirname) / "work"
            workdir.mkdir()

            completed = run_script(
                "confirm_stage.py", "--workdir", str(workdir), "--stage", "screenshot-method", "--method", "user-supplied"
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            preferences = json.loads((workdir / "用户偏好.json").read_text(encoding="utf-8"))
            self.assertEqual(preferences["choices"]["screenshot_method"], "user-supplied")

    def test_run_stage_build_auto_mode_applies_defaults_before_gate_check(self) -> None:
        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            workdir = make_confirmable_workdir(tmp_path, pending_application_field=True)
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "workdir": str(workdir),
                        "software_name": "演示任务管理系统",
                        "version": "V1.0",
                        "confirmation_mode": "auto",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "build")

            # 申请表仍有待确认字段：auto 模式补齐可默认门禁后，仍应停在数据门禁上。
            self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["requires_user_input"], True)
            self.assertIn("待用户确认", payload["outputs"]["issues"])
            business = json.loads((workdir / "草稿/业务理解.json").read_text(encoding="utf-8"))
            self.assertIs(business["user_confirmed"], True)


if __name__ == "__main__":
    unittest.main()
