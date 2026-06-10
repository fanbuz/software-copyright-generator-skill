#!/usr/bin/env python3
"""Manage confirmation mode and reusable user preferences for the workflow.

交互设计：
- 前置采集完成后，先向用户展示已保存偏好（--show），询问确认模式：
  interactive（逐项确认，默认）或 auto（按默认与已保存偏好直走）。
- 用户选择 auto 后（--set-mode auto），用 --apply-defaults 自动记录可默认的门禁；
  登记数据类内容（申请表待确认字段、业务理解草稿本身）仍需用户提供，不能被默认代替。
- 流程中的用户选择（确认模式、截图方式、服务地址等）保存到 `用户偏好.json`，
  下次在同一工作目录运行时直接复用。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import load_user_preferences, read_json, save_user_preferences
from confirm_stage import (
    confirm_application_fields,
    confirm_business,
    confirm_code_selection,
    confirm_environment,
    confirm_markdown,
    confirm_screenshot_method,
)


MODES = ("interactive", "auto")
AUTO_NOTE = "用户已选择默认模式，按已保存偏好自动确认"


def set_confirmation_mode(workdir: Path, mode: str, note: str) -> dict[str, Any]:
    if mode not in MODES:
        raise SystemExit(f"Unknown confirmation mode: {mode}; expected one of {MODES}")
    data = load_user_preferences(workdir)
    data["confirmation_mode"] = mode
    data["mode_note"] = note
    save_user_preferences(workdir, data)
    return data


def record_choices(workdir: Path, pairs: list[str]) -> dict[str, Any]:
    data = load_user_preferences(workdir)
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--record 需要 key=value 形式，收到：{pair}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"--record 的 key 不能为空：{pair}")
        data["choices"][key] = value.strip()
    save_user_preferences(workdir, data)
    return data


def stop_reason(exc: SystemExit) -> str:
    text = str(exc).replace("STOP_FOR_USER", "").replace("NEXT_ACTION:", "").strip()
    return text.splitlines()[0].strip() if text else "需要用户补充信息"


def gate_done(path: Path, key: str) -> bool:
    if not path.exists():
        return False
    data = read_json(path)
    return isinstance(data, dict) and bool(data.get(key))


def apply_defaults(workdir: Path, preferences: dict[str, Any]) -> dict[str, Any]:
    """Auto-confirm gates that have safe defaults; report what still needs the user.

    可默认的门禁：environment、screenshot-method（用已保存偏好，否则 skip）、
    business、code-selection、application-fields、markdown 的“确认动作”。
    不可默认的内容：草稿本身缺失、申请表仍有待用户确认字段、源码选择缺少理由。
    """
    draft = workdir / "草稿"
    auto_confirmed: list[str] = []
    already_confirmed: list[str] = []
    pending: list[dict[str, str]] = []

    if gate_done(workdir / "环境确认.json", "environment_confirmed"):
        already_confirmed.append("environment")
    else:
        confirm_environment(workdir, AUTO_NOTE)
        auto_confirmed.append("environment")

    if gate_done(workdir / "截图方式确认.json", "screenshot_method_confirmed"):
        already_confirmed.append("screenshot-method")
    else:
        method = str(preferences.get("choices", {}).get("screenshot_method") or "skip")
        confirm_screenshot_method(workdir, AUTO_NOTE, method)
        auto_confirmed.append(f"screenshot-method({method})")

    business_path = draft / "业务理解.json"
    if not business_path.exists():
        pending.append({"stage": "business", "reason": "缺少 草稿/业务理解.json，需先生成业务理解草稿"})
    elif read_json(business_path).get("user_confirmed"):
        already_confirmed.append("business")
    else:
        confirm_business(workdir, AUTO_NOTE)
        auto_confirmed.append("business")

    selection_path = draft / "代码文件选择.json"
    if not selection_path.exists():
        pending.append({"stage": "code-selection", "reason": "缺少 草稿/代码文件选择.json，需先生成并填写代码选择"})
    elif read_json(selection_path).get("user_confirmed"):
        already_confirmed.append("code-selection")
    else:
        try:
            confirm_code_selection(workdir, AUTO_NOTE)
            auto_confirmed.append("code-selection")
        except SystemExit as exc:
            pending.append({"stage": "code-selection", "reason": stop_reason(exc)})

    if gate_done(draft / "申请表字段确认.json", "application_fields_confirmed"):
        already_confirmed.append("application-fields")
    else:
        try:
            confirm_application_fields(workdir, AUTO_NOTE)
            auto_confirmed.append("application-fields")
        except SystemExit:
            pending.append(
                {"stage": "application-fields", "reason": "申请表信息仍包含待用户确认字段，默认模式不能代替用户填写登记数据"}
            )

    if gate_done(draft / "最终生成确认.json", "markdown_confirmed"):
        already_confirmed.append("markdown")
    else:
        try:
            confirm_markdown(workdir, AUTO_NOTE)
            auto_confirmed.append("markdown")
        except SystemExit as exc:
            pending.append({"stage": "markdown", "reason": stop_reason(exc)})

    return {
        "mode": "auto",
        "auto_confirmed": auto_confirmed,
        "already_confirmed": already_confirmed,
        "pending": pending,
        "preferences": str(workdir / "用户偏好.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="软件著作权申请资料")
    parser.add_argument("--set-mode", choices=list(MODES), help="设置确认模式：interactive 逐项确认 / auto 按默认直走")
    parser.add_argument("--note", default="用户已确认", help="设置模式或记录偏好时的说明")
    parser.add_argument("--record", action="append", default=[], metavar="KEY=VALUE", help="记录一个选择偏好，可重复")
    parser.add_argument("--show", action="store_true", help="输出当前已保存偏好，供下次运行复用")
    parser.add_argument("--apply-defaults", action="store_true", help="auto 模式下按默认与已保存偏好自动记录可默认门禁")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    if args.set_mode:
        set_confirmation_mode(workdir, args.set_mode, args.note)
    if args.record:
        record_choices(workdir, args.record)

    preferences = load_user_preferences(workdir)

    if args.apply_defaults:
        if preferences.get("confirmation_mode") != "auto":
            raise SystemExit(
                "STOP_FOR_USER\n"
                "NEXT_ACTION: 当前确认模式为 interactive。请先询问用户是否按默认直走；"
                "用户同意后运行 --set-mode auto 再执行 --apply-defaults。"
            )
        report = apply_defaults(workdir, preferences)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["pending"]:
            raise SystemExit(10)
        return

    print(json.dumps(preferences, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
