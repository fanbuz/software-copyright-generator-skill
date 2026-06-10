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
| `analysis` | 否 | 已存在的 `analysis/project.json` 路径；不填时使用 `workdir/analysis/project.json`。 |
| `model_context` | business 阶段可选 | 模型填写后的业务理解 JSON，用于生成 `业务理解.md/json`。缺失时阶段会返回 `requires_user_input=true`。 |
| `business_context` | draft 阶段可选 | 已确认的 `业务理解.json` 路径；不填时使用 `workdir/草稿/业务理解.json`。 |
| `code_selection` | draft 阶段可选 | 已确认的 `代码文件选择.json` 路径；不填时使用 `workdir/草稿/代码文件选择.json`。 |
| `answers` | draft 阶段可选 | 已确认的申请表字段 JSON。 |
| `manual_screenshot_dir` | screenshots 阶段可选 | 用户提供截图目录。 |
| `final_dir` | review 阶段可选 | 正式资料目录；不填时使用 `workdir/正式资料`。 |
| `forbidden_terms` | 否 | 最终复核需要检查的禁用词、旧名称或不应出现的模块词。 |
| `skip_preview` | 否 | build 阶段是否跳过本机 DOCX 预览检查。 |

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
- `screenshots`：整理用户提供截图并生成截图清单。
- `build`：在门禁齐备后生成正式 Word/TXT。
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
