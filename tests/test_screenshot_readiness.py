from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - http.server API
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args: object) -> None:
        pass


class _LocalServer:
    def __enter__(self) -> str:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}/"

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()


class ScreenshotReadinessTests(unittest.TestCase):
    def test_check_only_waits_for_web_service(self) -> None:
        base_url = f"http://127.0.0.1:{free_port()}/"

        completed = run_script("capture_screenshots.py", "--check-only", "--base-url", base_url)

        self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "waiting_service")
        self.assertIs(payload["service_reachable"], False)
        self.assertIn("启动 Web 服务", payload["next_action"])
        self.assertIn("Web 端服务", payload["note"])

    def test_check_only_reports_service_reachable(self) -> None:
        with _LocalServer() as base_url:
            completed = run_script("capture_screenshots.py", "--check-only", "--base-url", base_url)

        payload = json.loads(completed.stdout)
        self.assertIs(payload["service_reachable"], True)
        # Playwright 可选依赖：装了为 ready/0，没装为 playwright_missing/2。
        self.assertIn(payload["status"], {"ready", "playwright_missing"})
        self.assertIn(completed.returncode, {0, 2})

    def test_confirm_screenshot_ready_blocks_until_service_up(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            workdir = Path(dirname) / "work"
            workdir.mkdir()
            base_url = f"http://127.0.0.1:{free_port()}/"

            blocked = run_script(
                "confirm_stage.py", "--workdir", str(workdir), "--stage", "screenshot-ready", "--base-url", base_url
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("STOP_FOR_USER", blocked.stdout + blocked.stderr)
            self.assertIn("启动 Web 服务", blocked.stdout + blocked.stderr)
            self.assertFalse((workdir / "截图服务确认.json").exists())

            with _LocalServer() as live_url:
                confirmed = run_script(
                    "confirm_stage.py", "--workdir", str(workdir), "--stage", "screenshot-ready", "--base-url", live_url
                )
            self.assertEqual(confirmed.returncode, 0, confirmed.stdout + confirmed.stderr)
            data = json.loads((workdir / "截图服务确认.json").read_text(encoding="utf-8"))
            self.assertIs(data["screenshot_service_ready"], True)
            self.assertEqual(data["base_url"], live_url)

    def test_run_stage_screenshots_waits_for_web_service(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            workdir = tmp_path / "work"
            workdir.mkdir()
            (workdir / "截图方式确认.json").write_text(
                json.dumps({"screenshot_method": "chrome-devtools", "screenshot_method_confirmed": True}),
                encoding="utf-8",
            )
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "software-copyright-job.v1",
                        "workdir": str(workdir),
                        "base_url": f"http://127.0.0.1:{free_port()}/",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "screenshots")

            self.assertEqual(completed.returncode, 10, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIs(payload["requires_user_input"], True)
            self.assertIn("启动 Web 服务", payload["next_action"])
            readiness = json.loads(Path(payload["outputs"]["readiness"]).read_text(encoding="utf-8"))
            self.assertEqual(readiness["status"], "waiting_service")

    def test_run_stage_screenshots_skip_method_returns_note(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as dirname:
            tmp_path = Path(dirname)
            workdir = tmp_path / "work"
            workdir.mkdir()
            (workdir / "截图方式确认.json").write_text(
                json.dumps({"screenshot_method": "skip", "screenshot_method_confirmed": True}),
                encoding="utf-8",
            )
            manifest = tmp_path / "job.json"
            manifest.write_text(
                json.dumps({"schema_version": "software-copyright-job.v1", "workdir": str(workdir)}, ensure_ascii=False),
                encoding="utf-8",
            )

            completed = run_script("run_stage.py", "--manifest", str(manifest), "--stage", "screenshots")

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["outputs"]["status"], "skip")


if __name__ == "__main__":
    unittest.main()
