from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
    )


def create_demo_project(base: Path, file_count: int = 3, lines_per_file: int = 8) -> Path:
    project = base / "demo-task-system"
    (project / "src/pages").mkdir(parents=True)
    (project / "src/components").mkdir(parents=True)
    (project / "node_modules/ignored").mkdir(parents=True)
    (project / "dist").mkdir(parents=True)
    (project / "package.json").write_text(
        json.dumps(
            {
                "name": "demo-task-system",
                "version": "1.0.0",
                "dependencies": {"vue": "^3.0.0", "vite": "^5.0.0"},
                "scripts": {"dev": "vite"},
            }
        ),
        encoding="utf-8",
    )
    (project / "README.md").write_text("# 演示任务管理系统\n\n用于演示任务创建、列表查看和状态流转。\n", encoding="utf-8")
    (project / "src/main.ts").write_text("import { createApp } from 'vue'\ncreateApp({}).mount('#app')\n", encoding="utf-8")
    (project / "src/router.ts").write_text("export const routes = [{ path: '/tasks' }, { path: '/reports' }]\n", encoding="utf-8")
    for index in range(file_count):
        lines = [f"export const demoValue{index}_{line} = '{line}'" for line in range(lines_per_file)]
        (project / f"src/pages/page{index}.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (project / "node_modules/ignored/index.ts").write_text("export const ignored = true\n", encoding="utf-8")
    (project / "dist/bundle.js").write_text("console.log('ignored')\n", encoding="utf-8")
    return project


class WorkflowContractTests(unittest.TestCase):
    def test_analyze_project_writes_stable_contract(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            project = create_demo_project(tmp_path)
            out = tmp_path / "work/analysis/project.json"

            completed = run_script("analyze_project.py", "--project", str(project), "--out", str(out))

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "analysis.v1")
            self.assertEqual(data["project_name"], "demo-task-system")
            self.assertEqual(data["software_name_candidate"], "demo task system")
            self.assertIn("Vue", data["frameworks"])
            self.assertIn("/tasks", data["routes"])
            categorized = data["source"]["categorized_files"]
            self.assertIn("src/main.ts", categorized["entry"])
            self.assertTrue(all("node_modules" not in path for paths in categorized.values() for path in paths))
            self.assertEqual(data["contract"]["required_for"], ["business", "code-selection", "draft"])

    def test_code_extraction_supports_confirmed_line_ranges(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            project = create_demo_project(tmp_path, file_count=1, lines_per_file=12)
            work = tmp_path / "work/草稿"
            work.mkdir(parents=True)
            selection = work / "代码文件选择.json"
            selection.write_text(
                json.dumps(
                    {
                        "selection_required": True,
                        "user_confirmed": True,
                        "model_selection_required": True,
                        "files": [
                            {
                                "path": "src/pages/page0.ts",
                                "selected": True,
                                "start_line": 3,
                                "end_line": 6,
                                "line_count": 12,
                                "model_reason": "演示页面包含任务列表展示逻辑。",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script(
                "extract_code_material.py",
                "--project",
                str(project),
                "--software-name",
                "演示任务管理系统",
                "--version",
                "V1.0",
                "--out-dir",
                str(work),
                "--selection",
                str(selection),
                "--lines-per-page",
                "5",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            manifest = json.loads((work / "代码提取清单.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["files"][0]["selected_line_start"], 3)
            self.assertEqual(manifest["files"][0]["selected_line_end"], 6)
            output = (work / "代码-全部.md").read_text(encoding="utf-8")
            self.assertIn("demoValue0_2", output)
            self.assertIn("demoValue0_5", output)
            self.assertNotIn("demoValue0_1", output)
            self.assertNotIn("demoValue0_6", output)

    def test_run_stage_scan_reads_manifest_and_outputs_json(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            project = create_demo_project(tmp_path)
            workdir = tmp_path / "work"
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "project_dir": str(project),
                        "workdir": str(workdir),
                        "software_name": "演示任务管理系统",
                        "version": "V1.0",
                        "confirmations": {"environment": True},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "scan")

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["ok"], True)
            self.assertEqual(payload["stage"], "scan")
            self.assertIs(payload["requires_user_input"], False)
            self.assertTrue(Path(payload["outputs"]["analysis"]).exists())

    def test_run_stage_review_reports_missing_package_as_json(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            workdir = tmp_path / "work"
            workdir.mkdir()
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "project_dir": str(tmp_path / "demo-project"),
                        "workdir": str(workdir),
                        "software_name": "演示任务管理系统",
                        "version": "V1.0",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "review")

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["ok"], True)
            review = payload["outputs"]["review"]
            self.assertIs(review["ok"], False)
            self.assertEqual(review["missing"], ["info", "manual", "source"])

    def test_run_stage_code_selection_stops_with_candidate_outputs(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            project = create_demo_project(tmp_path)
            workdir = tmp_path / "work"
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "project_dir": str(project),
                        "workdir": str(workdir),
                        "software_name": "演示任务管理系统",
                        "version": "V1.0",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "code-selection")

            self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["requires_user_input"], True)
            selection_json = Path(payload["outputs"]["selection_json"])
            self.assertTrue(selection_json.exists())
            selection = json.loads(selection_json.read_text(encoding="utf-8"))
            self.assertEqual(selection["schema_version"], "code-selection.v1")
            self.assertIn("estimated_all_candidate_pages", selection)


if __name__ == "__main__":
    unittest.main()
