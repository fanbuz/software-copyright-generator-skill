---
name: software-copyright-generator
description: Use when generating, repairing, reviewing, or packaging Chinese software copyright application materials, including information forms, user manuals, source-code materials, screenshots, DOCX templates, and delivery checks.
allowed-tools: >
  Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
metadata:
  short-description: 生成和复核软著申请三件套
  author: software-copyright-generator contributors
  version: "1.0"
---

# Software Copyright Generator

本 skill 从真实项目生成和复核中国软件著作权申请材料。它的核心目标是让资料可追溯、可确认、可复核：先理解项目和业务口径，再确认登记字段、代码选择和截图方式，最后生成并检查 `信息采集表 + 用户手册 + 源代码`。

## 基本原则

- 输出目录默认使用当前工作目录下的 `软件著作权申请资料/`。
- 面向用户生成材料时，不把正式文件写入 `/tmp`、`/private/tmp` 或其他临时目录。
- 用户提出生成软著材料时，先输出前置采集表并等待用户填写；已明确提供同等信息时，先整理成同一口径再继续。
- 先生成 Markdown 草稿，用户确认后再生成 Word/TXT。
- 正式资料只写入 `软件著作权申请资料/正式资料/`。
- 代码材料必须来自真实源码，禁止编造代码。
- 截图必须来自真实系统页面或用户提供图片；不得用生成图片冒充系统截图。
- 软件全称和版本号必须在申请表、用户手册、源代码、文件名、页眉页脚中保持一致。
- 用户要求删除的模块词，要同步排查申请表、手册、目录、图注、源代码说明和生成报告。

## 强制门禁

凡是涉及用户选择、确认或补充信息的阶段，必须停住等待用户输入。收到确认后，用脚本记录门禁再继续：

```bash
python3 <skill-dir>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage <stage> --note "<用户确认内容>"
```

必须停住的阶段：

- `preflight`：用户填写软件全称、版本号、著作权人、开发完成日期、发表状态、仓库模式、代码位置、截图方式等前置信息。
- `environment`：完整 DOCX 环境缺失时，用户选择安装完整环境或使用基础 DOCX 继续。
- `project`：存在多个项目候选目录时，用户指定项目目录。
- `business`：业务理解草稿生成后，用户确认行业、目标用户、核心功能和申请口径。
- `application-fields`：申请表信息生成后，用户补全并确认登记字段。
- `code-selection`：代码文件候选清单生成后，用户确认或修改抽取文件。
- `screenshot-method`：用户在 Chrome DevTools MCP、Codex Computer Use、用户自行截图、暂不截图中选择一种。
- `markdown`：全部 Markdown 草稿完成后，用户确认可以生成正式 Word/TXT。

## 工作流

1. 前置采集：运行 `scripts/generate_input_form.py` 或 `scripts/run_stage.py --stage preflight`，向用户展示 `【请用户输入】` 表单，至少确认软件全称、版本号、著作权人、开发完成日期、发表状态、仓库模式、代码位置和截图方式；用户提交后记录 `preflight` 门禁。
2. 环境检查：运行 `scripts/check_environment.py --out-dir 软件著作权申请资料`，确认 Markdown、TXT、基础 DOCX 和可选 OpenXML 校验能力。
3. 定位项目：按前置采集表中的仓库模式和代码位置定位项目，避开依赖、构建产物、输出目录和隐藏目录；多个候选项目时询问用户。
4. 项目分析：运行 `scripts/analyze_project.py --project <项目目录> --out 软件著作权申请资料/analysis/project.json`。
5. 业务理解：用 `scripts/generate_business_context.py` 收集证据；模型阅读 README、PRD、路由、页面、接口和必要源码后写出业务理解 JSON，再生成 `草稿/业务理解.md/json` 并等待确认。
6. 登记字段：确认软件全称、版本号、著作权人、开发完成日期、首次发表状态、硬件环境、操作系统、开发工具、运行支撑环境、软件分类和技术特点。
7. 代码选择：运行 `scripts/propose_code_selection.py` 生成候选清单；模型按真实功能和运行逻辑选择源码文件，可填写 `start_line/end_line` 指定行段，写明理由并等待用户确认。
8. 草稿生成：运行 `scripts/extract_code_material.py`、`scripts/generate_application_info.py`、`scripts/generate_manual_draft.py`，生成代码、申请表信息和操作手册 Markdown。
9. 截图处理：按用户选择获取或整理截图；如果暂不截图，手册保留清晰可见的截图预留文字。
10. Markdown 确认：用户确认全部草稿后，记录 `markdown` 门禁。
11. 正式生成：运行 `scripts/build_docx_from_md.py --workdir 软件著作权申请资料 --software-name "<软件全称>" --version "<版本号>"`。
12. 最终复核：按 `references/final_review.md` 检查目标目录中的最终文件。

## 源代码材料规则

- 源程序材料使用真实源码文本，不使用截图、压缩代码、构建产物、依赖目录、临时脚本或第三方库主体。
- 大型项目按前 30 页和后 30 页连续代码组织；不足 60 页时提交全部候选源码。
- 每页默认不少于 50 行；不要靠空行或大段无关注释凑页数。
- 保留正常缩进和必要注释；清理尾随空格、连续多空行、密钥、token、账号密码、客户隐私和无关 license。
- 如只选择文件局部行段，必须由模型在 `代码文件选择.json` 写入 `start_line/end_line` 并说明选择理由，抽取清单会记录原始行号。
- 前后端都属于申报软件时，前段优先放前端入口、路由、页面、组件、接口封装，后段放后端 Controller、Service、实体、Mapper 和核心业务逻辑。
- 源代码 Word 页眉或页首必须包含软件全称和版本号，页码连续。

## 申请表和模板

- 用户提供历史 `信息采集表*.docx` 时，优先复制模板后局部替换值单元格和勾选框，不重建简化表。
- 可用 `scripts/fill_info_form_from_template.py` 套打 DOCX 模板。
- 开发完成日期、首次发表日期、首次发表城市等用户要求空着的字段必须保持空白。
- 申请表“主要功能和技术特点”要与用户手册章节范围一致。

## 用户手册规则

- 操作手册应像真实软件随附说明，不写研发说明、功能清单或生成过程说明。
- 采用传统结构：相关文档、说明、功能特点、系统要求、按真实页面/流程逐章操作、常见问题解答、术语表。
- 核心页面要写清入口、可见字段/按钮、常用操作、输入限制或异常提示、结果反馈和截图位置。
- 避免“进入方式/页面内容/操作步骤/操作规则/操作结果”这种字段模板堆砌。
- 避免营销口号和 AI 味；每段都要能回答“这个项目里这个功能具体做什么、用户看见什么、操作后有什么结果”。

## 推荐脚本

- `scripts/generate_input_form.py`：前置采集表 Markdown 和 JSON 字段契约。
- `scripts/analyze_project.py`：项目结构、语言、入口、路由、页面和源码统计。
- `scripts/generate_business_context.py`：业务理解证据和确认稿。
- `scripts/generate_application_info.py`：申请表信息草稿。
- `scripts/propose_code_selection.py`：代码候选清单。
- `scripts/extract_code_material.py`：代码材料分页和追溯清单。
- `scripts/generate_manual_draft.py`：用户手册草稿和自检记录。
- `scripts/build_docx_from_md.py`：正式 Word/TXT 生成。
- `scripts/fill_info_form_from_template.py`：历史申请表模板套打。
- `scripts/review_three_piece_package.py`：最终三件套 DOCX 复核。

## 完成前检查

- 三件套文件存在，文件名包含软件全称和版本号。
- 三份文档中的软件全称、版本号、著作权人和日期口径一致。
- 申请表、手册、目录、图注、源码说明无禁用词或旧项目残留。
- 用户手册截图来自真实系统页面或用户提供文件；暂不截图时有可见预留位。
- 代码材料能回溯到真实源码，页数、行数、页眉和页码满足当前申报口径。
- 已直接检查用户目标目录中的最终 Word/TXT，而不是只检查中间副本。
