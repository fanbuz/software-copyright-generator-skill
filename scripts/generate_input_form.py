#!/usr/bin/env python3
"""Generate the preflight input form for a software copyright job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORM_SCHEMA_VERSION = "preflight-input-form.v1"

FORM_SECTIONS: list[dict[str, Any]] = [
    {
        "title": "一、登记信息",
        "fields": [
            {
                "key": "software_name",
                "label": "软件全称",
                "required": True,
                "placeholder": "例如：演示任务管理系统",
                "help": "必须与申请表、用户手册、源代码材料、文件名保持一致。",
            },
            {
                "key": "software_short_name",
                "label": "软件简称",
                "required": False,
                "placeholder": "可选",
                "help": "没有简称可留空。",
            },
            {
                "key": "version",
                "label": "版本号",
                "required": True,
                "placeholder": "例如：V1.0",
                "help": "必须与正式材料中的版本号一致。",
            },
            {
                "key": "copyright_owner",
                "label": "著作权人",
                "required": True,
                "placeholder": "填写申请主体名称",
                "help": "按拟登记主体填写。",
            },
            {
                "key": "completion_date",
                "label": "开发完成日期",
                "required": True,
                "placeholder": "YYYY-MM-DD",
                "help": "如需留空，请明确写“留空”。",
            },
            {
                "key": "publication_status",
                "label": "发表状态",
                "required": True,
                "placeholder": "未发表/已发表",
                "help": "已发表时继续填写首次发表日期和城市。",
            },
            {
                "key": "first_publication_date",
                "label": "首次发表日期",
                "required": False,
                "placeholder": "YYYY-MM-DD，未发表可留空",
                "help": "仅在已发表时填写。",
            },
            {
                "key": "first_publication_city",
                "label": "首次发表城市",
                "required": False,
                "placeholder": "未发表可留空",
                "help": "仅在已发表时填写。",
            },
            {
                "key": "rights_acquisition",
                "label": "权利取得方式",
                "required": False,
                "placeholder": "原始取得/继受取得",
                "help": "不确定时留空，后续确认。",
            },
            {
                "key": "rights_scope",
                "label": "权利范围",
                "required": False,
                "placeholder": "全部权利/部分权利",
                "help": "不确定时留空，后续确认。",
            },
        ],
    },
    {
        "title": "二、仓库与代码",
        "fields": [
            {
                "key": "repository_mode",
                "label": "仓库模式",
                "required": True,
                "placeholder": "单体/前后分离/多仓库/其他",
                "help": "用于判断源码抽取范围和前后端材料顺序。",
            },
            {
                "key": "project_dir",
                "label": "项目根目录",
                "required": False,
                "placeholder": "单体仓库填写",
                "help": "单体仓库或当前目录可填写此项。",
            },
            {
                "key": "frontend_project_dir",
                "label": "前端仓库代码位置",
                "required": False,
                "placeholder": "前后分离项目填写",
                "help": "没有前端仓库可留空。",
            },
            {
                "key": "backend_project_dir",
                "label": "后端仓库代码位置",
                "required": False,
                "placeholder": "前后分离项目填写",
                "help": "没有后端仓库可留空。",
            },
            {
                "key": "additional_project_dirs",
                "label": "其他代码位置",
                "required": False,
                "placeholder": "多个路径用换行列出",
                "help": "如移动端、管理端、公共库等。",
            },
            {
                "key": "preferred_modules",
                "label": "优先纳入源码的模块",
                "required": False,
                "placeholder": "模块名或目录名",
                "help": "用于辅助代码候选清单排序。",
            },
            {
                "key": "excluded_modules",
                "label": "需要排除的目录或模块",
                "required": False,
                "placeholder": "目录名、模块名或旧名称",
                "help": "会同步用于申请表、手册、源码说明和复核。",
            },
            {
                "key": "forbidden_terms",
                "label": "不应出现在正式材料中的名称",
                "required": False,
                "placeholder": "多个词用顿号或换行列出",
                "help": "用于最终一致性检查。",
            },
        ],
    },
    {
        "title": "三、运行与截图",
        "fields": [
            {
                "key": "frontend_start_command",
                "label": "前端启动命令",
                "required": False,
                "placeholder": "例如：npm run dev",
                "help": "无法本地启动可写“暂不启动”。",
            },
            {
                "key": "backend_start_command",
                "label": "后端启动命令",
                "required": False,
                "placeholder": "例如：mvn spring-boot:run",
                "help": "无法本地启动可写“暂不启动”。",
            },
            {
                "key": "access_url",
                "label": "访问地址",
                "required": False,
                "placeholder": "例如：http://localhost:3000",
                "help": "用于截图或页面核对。",
            },
            {
                "key": "login_method",
                "label": "登录方式/测试账号提供方式",
                "required": False,
                "placeholder": "公开文本中不要填写口令",
                "help": "如需账号，由用户通过合适方式另行提供。",
            },
            {
                "key": "screenshot_method",
                "label": "截图方式",
                "required": True,
                "placeholder": "用户提供/浏览器自动/暂不截图",
                "help": "截图必须来自真实系统页面或用户提供图片。",
            },
            {
                "key": "manual_screenshot_dir",
                "label": "用户截图目录",
                "required": False,
                "placeholder": "用户提供截图时填写",
                "help": "目录内图片会整理到截图清单。",
            },
        ],
    },
    {
        "title": "四、模板与输出",
        "fields": [
            {
                "key": "info_form_template",
                "label": "信息采集表模板路径",
                "required": False,
                "placeholder": "没有模板可留空",
                "help": "已有模板时优先套打模板。",
            },
            {
                "key": "output_dir",
                "label": "输出目录",
                "required": False,
                "placeholder": "默认：软件著作权申请资料",
                "help": "正式资料会进入该目录下的正式资料子目录。",
            },
            {
                "key": "notes",
                "label": "其他说明",
                "required": False,
                "placeholder": "补充功能边界、申请口径或特殊要求",
                "help": "只写与本次材料生成直接相关的信息。",
            },
        ],
    },
]


def build_form_schema() -> dict[str, Any]:
    return {
        "schema_version": FORM_SCHEMA_VERSION,
        "title": "软著材料生成前置采集表",
        "sections": FORM_SECTIONS,
    }


def build_form_markdown() -> str:
    lines = [
        "【请用户输入】",
        "",
        "请先补充以下信息。无法确定的字段可以写“待确认”，不适用的字段可以留空。",
        "",
    ]
    for section in FORM_SECTIONS:
        lines.append(f"## {section['title']}")
        lines.append("")
        for field in section["fields"]:
            required = "（必填）" if field.get("required") else ""
            placeholder = f" {field['placeholder']}" if field.get("placeholder") else ""
            lines.append(f"{field['label']}：{required}{placeholder}")
        lines.append("")
    lines.extend(
        [
            "## 填写后确认",
            "",
            "- 以上信息用于确定申请表字段、源码抽取范围、用户手册章节和截图方式。",
            "- 正式生成前仍会分别确认业务口径、申请表字段、代码选择、截图方式和 Markdown 草稿。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_preflight_form(workdir: Path) -> dict[str, str]:
    workdir.mkdir(parents=True, exist_ok=True)
    form_path = workdir / "前置采集表.md"
    schema_path = workdir / "前置采集字段.json"
    form_path.write_text(build_form_markdown(), encoding="utf-8")
    schema_path.write_text(json.dumps(build_form_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"input_form": str(form_path), "input_schema": str(schema_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, help="Write the Markdown form to this path.")
    parser.add_argument("--json", action="store_true", help="Print the stable field contract as JSON.")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(build_form_schema(), ensure_ascii=False, indent=2))
        return

    markdown = build_form_markdown()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


if __name__ == "__main__":
    main()
