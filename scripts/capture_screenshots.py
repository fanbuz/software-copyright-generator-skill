#!/usr/bin/env python3
"""Best-effort screenshot helpers for operation manuals."""

from __future__ import annotations

import argparse
import json
import shutil
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

from common import ensure_dir, read_json, write_json


def safe_name(path: str) -> str:
    value = path.strip("/") or "home"
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value[:80] or "page"


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except Exception:
        return False
    return True


def probe_service(base_url: str, timeout: float = 5.0) -> dict[str, object]:
    """Check whether the user's web service answers at base_url.

    任何 HTTP 响应（包括 4xx/5xx）都视为服务可达；只有连接失败才视为未启动。
    """
    request = urllib.request.Request(base_url, method="GET", headers={"User-Agent": "software-copyright-generator/readiness"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"reachable": True, "status_code": int(response.status)}
    except urllib.error.HTTPError as exc:
        return {"reachable": True, "status_code": int(exc.code)}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


def check_readiness(base_url: str) -> dict[str, object]:
    """Build the screenshot readiness report shown to the user.

    自动截图目前仅支持浏览器可访问的 Web 端服务。状态优先级：
    服务未启动（waiting_service）→ 缺少 Playwright（playwright_missing）→ 就绪（ready）。
    """
    service = probe_service(base_url)
    has_playwright = playwright_available()
    blockers: list[str] = []
    if not service.get("reachable"):
        blockers.append(
            f"Web 服务尚不可访问：{base_url}。请在项目目录启动 Web 服务（如 npm run dev、python manage.py runserver），"
            "确认浏览器能打开该地址后回复确认。"
        )
    if not has_playwright:
        blockers.append("本机缺少 Playwright，无法浏览器自动截图。可安装 playwright 及浏览器内核，或改用用户自行截图。")
    if not service.get("reachable"):
        status = "waiting_service"
    elif not has_playwright:
        status = "playwright_missing"
    else:
        status = "ready"
    return {
        "status": status,
        "base_url": base_url,
        "service_reachable": bool(service.get("reachable")),
        "service_detail": service,
        "playwright_available": has_playwright,
        "next_action": "；".join(blockers) if blockers else "截图环境就绪，可以开始浏览器自动截图。",
        "note": "自动截图目前仅支持浏览器可访问的 Web 端服务；移动端、小程序、桌面端请由用户提供截图。",
    }


def collect_manual_screenshots(input_dir: Path, out_dir: Path) -> dict[str, object]:
    out_dir = ensure_dir(out_dir)
    screenshots = []
    errors = []
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    for index, path in enumerate(sorted(input_dir.iterdir()), start=1):
        if path.suffix.lower() not in allowed or not path.is_file():
            continue
        target = out_dir / f"{index:02d}-{safe_name(path.stem)}{path.suffix.lower()}"
        if path.resolve() != target.resolve():
            shutil.copy2(path, target)
        screenshots.append({"route": "", "url": "", "path": str(target), "source": str(path)})
    if not screenshots:
        errors.append({"error": f"no screenshot images found in {input_dir}"})
    manifest = {
        "status": "ok" if screenshots else "empty",
        "method": "user-supplied",
        "screenshots": screenshots,
        "errors": errors,
    }
    write_json(out_dir / "截图清单.json", manifest)
    return manifest


def capture_browser_screenshots(base_url: str, analysis_path: Path, out_dir: Path, max_pages: int = 8) -> dict[str, object]:
    from playwright.sync_api import sync_playwright

    analysis = read_json(analysis_path)
    paths = analysis.get("routes") or ["/"]
    clean_paths = []
    for path in paths:
        if isinstance(path, str) and path.startswith("/") and path not in clean_paths:
            clean_paths.append(path)
    clean_paths = clean_paths[:max_pages] or ["/"]

    out_dir = ensure_dir(out_dir)
    screenshots = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        for route in clean_paths:
            url = urljoin(base_url.rstrip("/") + "/", route.lstrip("/"))
            file_path = out_dir / f"{safe_name(route)}.png"
            try:
                page.goto(url, wait_until="networkidle", timeout=15_000)
                page.screenshot(path=str(file_path), full_page=True)
                screenshots.append({"route": route, "url": url, "path": str(file_path)})
            except Exception as exc:
                errors.append({"route": route, "url": url, "error": str(exc)})
        browser.close()

    manifest = {"status": "ok" if screenshots else "partial", "method": "browser", "base_url": base_url, "screenshots": screenshots, "errors": errors}
    write_json(out_dir / "截图清单.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url")
    parser.add_argument("--analysis")
    parser.add_argument("--out-dir", default="软件著作权申请资料/截图")
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--manual-dir", help="Collect user-supplied screenshots from this directory")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check screenshot readiness (web service reachability and Playwright availability)",
    )
    args = parser.parse_args()

    if args.check_only:
        if not args.base_url:
            raise SystemExit("--check-only requires --base-url（自动截图仅支持 Web 端服务）")
        readiness = check_readiness(args.base_url)
        print(json.dumps(readiness, ensure_ascii=False, indent=2))
        if readiness["status"] == "waiting_service":
            raise SystemExit(10)
        if readiness["status"] == "playwright_missing":
            raise SystemExit(2)
        return

    if args.manual_dir:
        manifest = collect_manual_screenshots(Path(args.manual_dir), Path(args.out_dir))
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        if not manifest["screenshots"]:
            raise SystemExit(3)
        return

    if not args.base_url or not args.analysis:
        raise SystemExit("Missing --base-url and --analysis unless --manual-dir is provided")

    readiness = check_readiness(args.base_url)
    if readiness["status"] == "waiting_service":
        print(json.dumps(readiness, ensure_ascii=False, indent=2))
        raise SystemExit(10)
    if readiness["status"] == "playwright_missing":
        print(json.dumps(readiness, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    manifest = capture_browser_screenshots(args.base_url, Path(args.analysis), Path(args.out_dir), args.max_pages)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if not manifest["screenshots"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
