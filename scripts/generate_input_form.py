#!/usr/bin/env python3
"""Generate the preflight input form for a software copyright job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORM_SCHEMA_VERSION = "preflight-input-form.v1"

SCENARIO_GUIDANCE = [
    "单体项目填写项目根目录；前后分离项目分别填写前端和后端代码位置；多仓库项目补充其他代码位置。",
    "移动端、小程序、桌面端或插件类项目按实际形态填写对应代码位置；没有的形态留空。",
    "已有申请表模板或历史材料时填写模板模式和模板路径；没有模板时使用本 skill 生成草稿。",
    "可以本地运行的项目填写启动命令和访问地址；无法运行时选择用户提供截图或暂不截图。",
    "源码材料默认使用真实源码并保留正常缩进；如需指定前后端顺序、页数口径或排除目录，应在源码材料字段中说明。",
]


def field(
    key: str,
    label: str,
    *,
    required: bool = False,
    placeholder: str = "",
    help_text: str = "",
    applies_when: str = "",
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "key": key,
        "label": label,
        "required": required,
        "placeholder": placeholder,
        "help": help_text,
    }
    if applies_when:
        data["applies_when"] = applies_when
    return data


FORM_SECTIONS: list[dict[str, Any]] = [
    {
        "title": "一、登记与权属",
        "fields": [
            field("software_name", "软件全称", required=True, placeholder="例如：演示任务管理系统", help_text="必须与申请表、用户手册、源代码材料、文件名保持一致。"),
            field("software_short_name", "软件简称", placeholder="可选", help_text="没有简称可留空。"),
            field("version", "版本号", required=True, placeholder="例如：V1.0", help_text="必须与正式材料中的版本号一致。"),
            field("copyright_owner", "著作权人", required=True, placeholder="填写申请主体名称", help_text="按拟登记主体填写。"),
            field("owner_type", "著作权人类型", placeholder="企业/个人/事业单位/其他", help_text="用于辅助申请表字段口径。"),
            field("applicant_contact", "申请联系人", placeholder="姓名或对接人，可选", help_text="只用于本次资料整理沟通。"),
            field("rights_acquisition", "权利取得方式", placeholder="原始取得/继受取得", help_text="不确定时写“待确认”。"),
            field("rights_scope", "权利范围", placeholder="全部权利/部分权利", help_text="不确定时写“待确认”。"),
            field("development_mode", "开发方式", placeholder="独立开发/合作开发/委托开发/下达任务开发", help_text="合作、委托或任务开发时，后续需确认对应证明材料口径。"),
            field("ownership_notes", "权属补充说明", placeholder="可选", help_text="填写与权利归属直接相关的补充说明。"),
        ],
    },
    {
        "title": "二、开发与发表",
        "fields": [
            field("completion_date", "开发完成日期", required=True, placeholder="YYYY-MM-DD", help_text="如需留空，请明确写“留空”。"),
            field("publication_status", "发表状态", required=True, placeholder="未发表/已发表", help_text="已发表时继续填写首次发表日期和城市。"),
            field("first_publication_date", "首次发表日期", placeholder="YYYY-MM-DD，未发表可留空", help_text="仅在已发表时填写。"),
            field("first_publication_city", "首次发表城市", placeholder="未发表可留空", help_text="仅在已发表时填写。"),
            field("software_category", "软件分类", placeholder="应用软件/系统软件/支撑软件/嵌入式软件/其他", help_text="用于申请表软件分类和手册说明。"),
            field("hardware_environment", "硬件环境", placeholder="例如：通用 PC、服务器、移动终端", help_text="用于申请表运行环境字段。"),
            field("os_environment", "操作系统", placeholder="例如：Windows、macOS、Linux、Android、iOS", help_text="按实际运行环境填写。"),
            field("runtime_environment", "运行环境/支撑软件", placeholder="例如：JDK、Node.js、浏览器、数据库、中间件", help_text="用于申请表和手册系统要求。"),
            field("development_tools", "开发工具", placeholder="例如：IDE、构建工具、数据库工具", help_text="可根据项目依赖和用户确认补全。"),
            field("version_history", "版本历史/本次申报版本说明", placeholder="首次申报/升级版本/补充登记", help_text="用于确认本次材料是否只覆盖当前版本。"),
        ],
    },
    {
        "title": "三、项目形态与仓库",
        "fields": [
            field("repository_mode", "仓库模式", required=True, placeholder="单体/前后分离/多仓库/其他", help_text="用于判断源码抽取范围和前后端材料顺序。"),
            field("project_dir", "项目根目录", placeholder="单体仓库填写", help_text="单体仓库或当前目录可填写此项。", applies_when="仓库模式为单体或当前目录就是完整项目。"),
            field("frontend_project_dir", "前端仓库代码位置", placeholder="前后分离项目填写", help_text="没有前端仓库可留空。", applies_when="仓库模式为前后分离或多仓库且包含前端。"),
            field("backend_project_dir", "后端仓库代码位置", placeholder="前后分离项目填写", help_text="没有后端仓库可留空。", applies_when="仓库模式为前后分离或多仓库且包含后端。"),
            field("mobile_project_dir", "移动端代码位置", placeholder="Android/iOS/Flutter/React Native 项目路径", help_text="没有移动端可留空。", applies_when="申报软件包含移动端。"),
            field("mini_program_project_dir", "小程序代码位置", placeholder="微信/支付宝/其他小程序项目路径", help_text="没有小程序可留空。", applies_when="申报软件包含小程序端。"),
            field("desktop_project_dir", "桌面端代码位置", placeholder="Electron/Qt/.NET/其他桌面端项目路径", help_text="没有桌面端可留空。", applies_when="申报软件包含桌面端。"),
            field("additional_project_dirs", "其他代码位置", placeholder="多个路径用换行列出", help_text="如管理端、公共库、插件、嵌入式固件等。"),
            field("repository_snapshot", "仓库快照/分支/提交", placeholder="分支名、tag、commit 或打包日期", help_text="用于保证材料可回溯到固定代码版本。"),
            field("dependency_policy", "依赖与第三方代码处理", placeholder="排除 node_modules、vendor、构建产物等", help_text="说明第三方依赖、生成文件和构建产物的排除口径。"),
            field("excluded_modules", "需要排除的目录或模块", placeholder="目录名、模块名或旧名称", help_text="会同步用于申请表、手册、源码说明和复核。"),
        ],
    },
    {
        "title": "四、业务范围与用户手册",
        "fields": [
            field("business_domain", "业务领域", placeholder="例如：办公协同、生产管理、数据分析", help_text="用于业务理解和申请表主要功能描述。"),
            field("target_users", "目标用户", placeholder="系统管理员、业务人员、外部用户等", help_text="用于用户手册角色视角。"),
            field("user_roles", "用户角色", placeholder="多个角色用换行列出", help_text="用于组织手册章节和截图页面。"),
            field("business_modules", "申报范围内的业务模块", placeholder="模块名、菜单名或功能域", help_text="只填写本次材料要覆盖的功能。"),
            field("out_of_scope_modules", "不纳入本次材料的模块", placeholder="模块名或说明", help_text="用于避免手册和源码材料越界。"),
            field("core_workflows", "核心操作流程", placeholder="例如：创建任务 -> 审批 -> 查询报表", help_text="用于生成操作手册章节。"),
            field("manual_chapter_preference", "用户手册章节偏好", placeholder="按角色/按菜单/按业务流程/按端划分", help_text="不确定时由模型按项目结构建议。"),
            field("terminology", "专有名词或术语", placeholder="术语及含义", help_text="用于手册术语表和说明一致性。"),
        ],
    },
    {
        "title": "五、源码材料",
        "fields": [
            field("source_material_strategy", "源码材料策略", placeholder="自动建议/用户指定/前后端混合/仅后端/仅前端", help_text="代码必须来自真实源码，不使用依赖目录、构建产物或截图。"),
            field("preferred_modules", "优先纳入源码的模块", placeholder="模块名、目录名或文件类型", help_text="用于辅助代码候选清单排序。"),
            field("source_order_preference", "源码排列顺序", placeholder="前端在前/后端在前/按模块/按运行链路", help_text="前后端都申报时需要确认。"),
            field("page_rule", "页数口径", placeholder="不足 60 页提交全部；超过 60 页取前后各 30 页", help_text="如当地或代理口径不同，在此说明。"),
            field("line_rule", "每页行数口径", placeholder="默认每页 50 行", help_text="不通过删除注释、压缩空格或混淆来凑页数。"),
            field("partial_file_policy", "局部文件抽取口径", placeholder="允许/不允许指定 start_line/end_line", help_text="用于大文件只抽取关键连续行段时确认。"),
            field("source_exclusion_policy", "源码排除口径", placeholder="依赖、构建产物、临时脚本、密钥配置、测试数据等", help_text="用于生成代码候选和最终检查。"),
        ],
    },
    {
        "title": "六、运行与截图",
        "fields": [
            field("frontend_start_command", "前端启动命令", placeholder="例如：npm run dev", help_text="无法本地启动可写“暂不启动”。", applies_when="项目包含前端或页面端。"),
            field("backend_start_command", "后端启动命令", placeholder="例如：mvn spring-boot:run", help_text="无法本地启动可写“暂不启动”。", applies_when="项目包含后端服务。"),
            field("mobile_run_method", "移动端运行方式", placeholder="模拟器/真机/用户提供截图", help_text="没有移动端可留空。", applies_when="申报软件包含移动端。"),
            field("mini_program_run_method", "小程序运行方式", placeholder="开发者工具/体验版/用户提供截图", help_text="没有小程序可留空。", applies_when="申报软件包含小程序端。"),
            field("access_url", "访问地址", placeholder="例如：http://localhost:3000", help_text="用于截图或页面核对。"),
            field("login_method", "登录方式/测试账号提供方式", placeholder="公开文本中不要填写口令", help_text="如需账号，由用户通过合适方式另行提供。"),
            field("screenshot_method", "截图方式", required=True, placeholder="用户提供/浏览器自动/暂不截图", help_text="截图必须来自真实系统页面或用户提供图片。"),
            field("screenshot_pages", "需要截图的页面/流程", placeholder="登录页、首页、核心业务页面、查询页、报表页等", help_text="用于形成截图清单和手册插图位置。"),
            field("manual_screenshot_dir", "用户截图目录", placeholder="用户提供截图时填写", help_text="目录内图片会整理到截图清单。", applies_when="截图方式为用户提供。"),
            field("runtime_blockers", "运行限制或阻塞", placeholder="缺少环境、无法登录、依赖服务不可用等", help_text="用于决定截图方案和手册预留。"),
        ],
    },
    {
        "title": "七、模板与输出",
        "fields": [
            field("template_mode", "模板模式", placeholder="使用用户模板/使用默认模板/只生成 Markdown", help_text="已有申请表模板时优先套打模板。"),
            field("info_form_template", "信息采集表模板路径", placeholder="没有模板可留空", help_text="已有模板时优先套打模板。", applies_when="模板模式为使用用户模板。"),
            field("legacy_material_dir", "已有材料目录", placeholder="历史申请表、手册或源码材料目录", help_text="用于参考结构和字段，不直接照搬旧内容。"),
            field("output_dir", "输出目录", placeholder="默认：软件著作权申请资料", help_text="正式资料会进入该目录下的正式资料子目录。"),
            field("output_formats", "输出格式", placeholder="Markdown/DOCX/TXT/PDF 预览", help_text="正式交付以当前支持能力和用户要求为准。"),
            field("docx_preview_policy", "DOCX 预览与校验方式", placeholder="本机预览/跳过预览/用户自行检查", help_text="用于决定 build 阶段是否执行预览检查。"),
            field("notes", "其他说明", placeholder="补充功能边界、申请口径或特殊要求", help_text="只写与本次材料生成直接相关的信息。"),
        ],
    },
    {
        "title": "八、正式资料检查",
        "fields": [
            field("forbidden_terms", "不应出现在正式材料中的名称", placeholder="多个词用顿号或换行列出", help_text="用于最终一致性检查。"),
            field("cleanup_check_terms", "正式资料清理检查词", placeholder="旧系统名、旧模块名、示例名、无关公司名等", help_text="用于复核申请表、手册、源码说明、目录和图注。"),
            field("consistency_focus", "一致性重点", placeholder="软件全称、版本号、著作权人、日期、模块名、截图标题", help_text="用于最终复核优先检查项。"),
            field("delivery_checklist", "交付检查要求", placeholder="文件名、页眉页脚、页码、页数、截图来源、源码追溯等", help_text="用于最终交付前人工确认。"),
        ],
    },
]


def build_form_schema() -> dict[str, Any]:
    return {
        "schema_version": FORM_SCHEMA_VERSION,
        "title": "软著材料生成前置采集表",
        "scenario_guidance": SCENARIO_GUIDANCE,
        "sections": FORM_SECTIONS,
    }


def build_form_markdown() -> str:
    lines = [
        "【请用户输入】",
        "",
        "请先补充以下信息。无法确定的字段可以写“待确认”，不适用的字段可以留空。",
        "",
        "## 场景填写提示",
        "",
    ]
    for item in SCENARIO_GUIDANCE:
        lines.append(f"- {item}")
    lines.append("")
    for section in FORM_SECTIONS:
        lines.append(f"## {section['title']}")
        lines.append("")
        for field in section["fields"]:
            required = "（必填）" if field.get("required") else ""
            placeholder = f" {field['placeholder']}" if field.get("placeholder") else ""
            lines.append(f"{field['label']}：{required}{placeholder}")
            if field.get("applies_when"):
                lines.append(f"  适用场景：{field['applies_when']}")
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
