# Job Manifest 编排协议

`software-copyright-job.v1` 用于让上层服务以单个 JSON 文件描述一次软著材料生成任务。manifest 只描述任务输入、确认状态和复核选项，不承载真实业务资料。

## 最小示例

前置采集阶段只需要 `workdir`：

```json
{
  "schema_version": "software-copyright-job.v1",
  "workdir": "/path/to/output/软件著作权申请资料"
}
```

用户提交表单后，再进入后续阶段：

```json
{
  "schema_version": "software-copyright-job.v1",
  "project_dir": "/path/to/demo-project",
  "workdir": "/path/to/output/软件著作权申请资料",
  "software_name": "演示任务管理系统",
  "version": "V1.0",
  "confirmations": {
    "environment": true
  },
  "forbidden_terms": ["旧系统名称"],
  "skip_preview": true
}
```

## 字段说明

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema_version` | 是 | 固定为 `software-copyright-job.v1`。 |
| `workdir` | 是 | 本次资料生成工作目录，默认结构仍为 `草稿/`、`截图/`、`正式资料/`。 |
| `project_dir` | scan 及后续阶段必填 | 待分析的软件项目目录。 |
| `software_name` | business 及后续阶段必填 | 用户确认的软件全称，正式文件名、页眉和正文一致性检查以此为准。 |
| `version` | 否 | 申报版本号，未填时使用 `V1.0`。 |
| `repository_mode` | 否 | 仓库模式，可取单体、前后分离、多仓库或其他，用于上层服务定位项目和解释源码范围。 |
| `frontend_project_dir` | 否 | 前端仓库代码位置，前后分离项目可填。 |
| `backend_project_dir` | 否 | 后端仓库代码位置，前后分离项目可填。 |
| `publication_status` | 否 | 发表状态，申请表字段生成时用于提示待确认信息。 |
| `completion_date` | 否 | 开发完成日期，申请表字段生成时用于提示待确认信息。 |
| `copyright_owner` | 否 | 著作权人，申请表字段生成时用于提示待确认信息。 |
| `development_mode` | 否 | 开发方式，如独立开发、合作开发、委托开发或下达任务开发。 |
| `software_category` | 否 | 软件分类，用于申请表和手册口径。 |
| `hardware_environment` | 否 | 硬件环境。 |
| `runtime_environment` | 否 | 运行环境或支撑软件。 |
| `repository_snapshot` | 否 | 分支、tag、commit 或打包日期，用于代码材料可追溯。 |
| `mobile_project_dir` | 否 | 移动端代码位置。 |
| `mini_program_project_dir` | 否 | 小程序代码位置。 |
| `desktop_project_dir` | 否 | 桌面端代码位置。 |
| `business_modules` | 否 | 本次申报范围内的业务模块。 |
| `user_roles` | 否 | 手册中的主要用户角色。 |
| `core_workflows` | 否 | 需要写入用户手册的核心操作流程。 |
| `source_material_strategy` | 否 | 源码材料策略，如自动建议、用户指定、前后端混合等。 |
| `page_rule` | 否 | 源码和文档页数口径。 |
| `screenshot_pages` | 否 | 需要截图的页面或流程。 |
| `template_mode` | 否 | 模板模式，如用户模板、默认模板或只生成 Markdown。 |
| `output_formats` | 否 | 期望输出格式。 |
| `cleanup_check_terms` | 否 | 正式资料清理检查词。 |
| `analysis` | 否 | 已存在的 `analysis/project.json` 路径；不填时使用 `workdir/analysis/project.json`。 |
| `model_context` | business 阶段可选 | 模型填写后的业务理解 JSON，用于生成 `业务理解.md/json`。缺失时阶段会返回 `requires_user_input=true`。 |
| `business_context` | draft 阶段可选 | 已确认的 `业务理解.json` 路径；不填时使用 `workdir/草稿/业务理解.json`。 |
| `code_selection` | draft 阶段可选 | 已确认的 `代码文件选择.json` 路径；不填时使用 `workdir/草稿/代码文件选择.json`。 |
| `answers` | draft 阶段可选 | 已确认的申请表字段 JSON。 |
| `manual_screenshot_dir` | screenshots 阶段可选 | 用户提供截图目录。 |
| `base_url` | screenshots 阶段可选 | Web 服务访问地址，用于浏览器自动截图（仅支持 Web 端服务）；服务不可达时阶段返回 `requires_user_input=true`，提示用户先启动 Web 服务。 |
| `max_pages` | screenshots 阶段可选 | 浏览器自动截图的最大页面数，默认 8。 |
| `final_dir` | review 阶段可选 | 正式资料目录；不填时使用 `workdir/正式资料`。 |
| `forbidden_terms` | 否 | 最终复核需要检查的禁用词、旧名称或不应出现的模块词。 |
| `skip_preview` | 否 | build 阶段是否跳过本机 DOCX 预览检查。 |
| `confirmation_mode` | 否 | 确认模式。`auto` 表示用户已授权按默认直走：build 阶段先按默认与 `用户偏好.json` 自动补齐可默认门禁，再检查剩余门禁；登记数据类门禁仍需用户提供。缺省为 `interactive` 逐项确认。 |

## 阶段入口

统一入口为：

```bash
python3 scripts/run_stage.py --manifest job.json --stage scan
```

支持阶段：

- `preflight`：生成前置采集表和字段契约，停止并等待用户填写。
- `scan`：生成 `analysis/project.json`。
- `business`：生成业务理解证据、模板或确认稿。
- `code-selection`：生成代码候选清单和选择 JSON。
- `draft`：生成代码、申请表、操作手册 Markdown 草稿。
- `screenshots`：整理用户提供截图，或在 Web 服务可达时浏览器自动截图并生成截图清单；服务未启动时写入 `截图/截图就绪检查.json` 并返回 `requires_user_input=true`，等待用户启动 Web 服务后重试（自动截图仅支持 Web 端服务）。
- `build`：在门禁齐备后生成正式 Word/TXT；`confirmation_mode=auto` 时先自动补齐可默认门禁，输出包含 `auto_confirm` 报告。
- `review`：复核正式三件套并输出 JSON。

## 输出约定

每个阶段输出 JSON：

```json
{
  "ok": true,
  "stage": "scan",
  "requires_user_input": false,
  "outputs": {
    "analysis": "/path/to/软件著作权申请资料/analysis/project.json"
  }
}
```

需要用户确认时返回：

```json
{
  "ok": false,
  "stage": "business",
  "requires_user_input": true,
  "next_action": "business confirmation required",
  "outputs": {
    "business_md": "/path/to/业务理解.md"
  }
}
```

退出码：

- `0`：阶段完成。
- `10`：阶段正常停止，等待用户确认或补充信息。
- `1`：执行失败。
- `2`：参数或阶段名称错误。

## 向后兼容

manifest 入口不替代现有脚本参数。上层服务可以逐步接入 `run_stage.py`，人工使用仍可直接调用各脚本。新增字段应保持可选；破坏性字段变更需要升级 `schema_version`。
