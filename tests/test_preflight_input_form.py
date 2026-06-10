from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        text=True,
        capture_output=True,
    )


class PreflightInputFormTests(unittest.TestCase):
    def test_cli_prints_required_user_input_markdown(self) -> None:
        completed = run_script("generate_input_form.py")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("【请用户输入】", completed.stdout)
        for label in [
            "软件全称：",
            "版本号：",
            "著作权人：",
            "开发完成日期：",
            "发表状态：",
            "仓库模式：",
            "前端仓库代码位置：",
            "后端仓库代码位置：",
        ]:
            self.assertIn(label, completed.stdout)

    def test_cli_json_exposes_stable_field_contract(self) -> None:
        completed = run_script("generate_input_form.py", "--json")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema_version"], "preflight-input-form.v1")
        fields = [field for section in payload["sections"] for field in section["fields"]]
        field_keys = {field["key"] for field in fields}
        self.assertTrue(
            {
                "software_name",
                "version",
                "copyright_owner",
                "completion_date",
                "publication_status",
                "repository_mode",
                "frontend_project_dir",
                "backend_project_dir",
            }.issubset(field_keys)
        )
        required_keys = {field["key"] for field in fields if field.get("required")}
        self.assertIn("software_name", required_keys)
        self.assertIn("repository_mode", required_keys)

    def test_cli_json_covers_common_project_and_material_scenarios(self) -> None:
        completed = run_script("generate_input_form.py", "--json")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("scenario_guidance", payload)
        section_titles = {section["title"] for section in payload["sections"]}
        self.assertTrue(
            {
                "一、登记与权属",
                "二、开发与发表",
                "三、项目形态与仓库",
                "四、业务范围与用户手册",
                "五、源码材料",
                "六、运行与截图",
                "七、模板与输出",
                "八、正式资料检查",
            }.issubset(section_titles)
        )
        fields = [field for section in payload["sections"] for field in section["fields"]]
        field_keys = {field["key"] for field in fields}
        expected_keys = {
            "development_mode",
            "software_category",
            "hardware_environment",
            "runtime_environment",
            "repository_snapshot",
            "mobile_project_dir",
            "mini_program_project_dir",
            "desktop_project_dir",
            "business_modules",
            "user_roles",
            "core_workflows",
            "source_material_strategy",
            "page_rule",
            "screenshot_pages",
            "template_mode",
            "output_formats",
            "cleanup_check_terms",
        }
        self.assertTrue(expected_keys.issubset(field_keys))
        conditional_fields = {field["key"] for field in fields if field.get("applies_when")}
        self.assertIn("mobile_project_dir", conditional_fields)
        self.assertIn("template_mode", field_keys)

    def test_run_stage_preflight_writes_form_to_workdir(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            manifest = tmp_path / "job.json"
            workdir = tmp_path / "work"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "workdir": str(workdir),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "preflight")

            self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["stage"], "preflight")
            self.assertTrue(payload["requires_user_input"])
            form_path = Path(payload["outputs"]["input_form"])
            schema_path = Path(payload["outputs"]["input_schema"])
            self.assertTrue(form_path.exists())
            self.assertTrue(schema_path.exists())
            self.assertIn("【请用户输入】", form_path.read_text(encoding="utf-8"))

    def test_confirm_stage_records_preflight_gate(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            workdir = Path(dirname) / "work"

            completed = run_script(
                "confirm_stage.py",
                "--workdir",
                str(workdir),
                "--stage",
                "preflight",
                "--note",
                "用户已提交前置采集表",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads((workdir / "前置采集确认.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["preflight_confirmed"])
            self.assertEqual(payload["confirmation_note"], "用户已提交前置采集表")


if __name__ == "__main__":
    unittest.main()
