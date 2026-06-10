# Software Copyright Generator Skill

`software-copyright-generator` 是一个用于生成、整理和复核中国软件著作权申请材料的 Codex skill。它以项目证据为输入，通过确认门禁把业务理解、申请表信息、用户手册、源代码材料和截图清单串成可追溯流程，最终输出信息采集表、用户手册和源代码材料。

## 能力范围

- 扫描项目结构、语言、入口、路由、页面、组件、接口和源码统计。
- 生成业务理解证据和模型填写模板，要求用户确认行业、目标用户、核心功能和手册模块。
- 生成用户前置采集表，先收集软件全称、版本号、著作权人、日期、仓库模式、代码位置和截图方式。
- 生成申请表信息 Markdown 草稿，并在正式生成前检查待确认字段。
- 生成源代码候选清单，要求模型选择理由和用户确认，再按页数规则输出全部源码或前后 30 页。
- 生成段落化用户手册草稿，保留截图预留或整理用户提供截图。
- 从确认后的 Markdown 生成 Word/TXT 正式资料。
- 对正式资料目录进行三件套完整性、一致性、禁用词和 DOCX 基础结构复核。
- 通过 `run_stage.py` 支持上层服务按 manifest 编排单阶段执行。

## 安装

将仓库作为 Codex skill 安装到本地 skill 目录，例如：

```bash
mkdir -p ~/.codex/skills
git clone git@github.com:fanbuz/software-copyright-generator-skill.git ~/.codex/skills/software-copyright-generator
```

安装后重启 Codex，或在新线程中触发 skill。skill 名称必须与 [SKILL.md](SKILL.md) frontmatter 保持一致：

```text
software-copyright-generator
```

## 依赖

- Python 3.10+
- 可选：`python-docx`，用于更完整的 DOCX 生成、模板套打和正式资料复核。
- 可选：Playwright，用于在具备运行系统和访问权限时采集页面截图。
- 可选：pandoc、Office、LibreOffice 或其他本地工具，用于额外预览和人工校验。

缺少 `python-docx` 时，代码材料可走基础 OOXML 兜底；模板套打和 DOCX 深度复核会提示能力限制。

## 最小使用路径

收到“做一下软著生成”这类请求时，先生成前置采集表并交给用户填写：

```bash
python3 ~/.codex/skills/software-copyright-generator/scripts/generate_input_form.py --out 软件著作权申请资料/前置采集表.md
```

表单开头为：

```text
【请用户输入】

软件全称：
版本号：
著作权人：
开发完成日期：
发表状态：
仓库模式：
前端仓库代码位置：
后端仓库代码位置：
...
```

用户提交后记录前置采集门禁：

```bash
python3 ~/.codex/skills/software-copyright-generator/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage preflight --note "用户已提交前置采集表"
```

之后在待处理项目所在目录运行：

```bash
python3 ~/.codex/skills/software-copyright-generator/scripts/check_environment.py --out-dir 软件著作权申请资料
python3 ~/.codex/skills/software-copyright-generator/scripts/analyze_project.py --project . --out 软件著作权申请资料/analysis/project.json
python3 ~/.codex/skills/software-copyright-generator/scripts/generate_business_context.py --project . --analysis 软件著作权申请资料/analysis/project.json --software-name "演示任务管理系统"
```

业务理解、申请表字段、代码选择、截图方式和最终 Markdown 都是确认门禁。每次用户确认后记录：

```bash
python3 ~/.codex/skills/software-copyright-generator/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage business --note "用户已确认业务口径"
```

正式生成前运行：

```bash
python3 ~/.codex/skills/software-copyright-generator/scripts/build_docx_from_md.py --workdir 软件著作权申请资料 --software-name "演示任务管理系统" --version "V1.0"
```

正式输出位于：

```text
软件著作权申请资料/正式资料/
```

## 服务化调用

上层服务可以用 manifest 调用单阶段：

```bash
python3 scripts/run_stage.py --manifest job.json --stage preflight
python3 scripts/run_stage.py --manifest job.json --stage scan
```

manifest 详见 [references/job_manifest.md](references/job_manifest.md)。阶段需要用户输入时会返回 JSON：

```json
{
  "ok": false,
  "requires_user_input": true,
  "next_action": "business confirmation required"
}
```

## 软著规则映射

本 skill 的文档生成遵循《计算机软件著作权登记办法》第十条关于“软件鉴别材料”的要求，并把常见材料口径落到以下规则：

| 生成内容 | 对应规则 | 本 skill 的落地方式 |
| --- | --- | --- |
| 源代码材料 | 第十条要求软件鉴别材料包括程序鉴别材料；一般提交源程序前、后各连续 30 页，不足 60 页时提交全部。 | `extract_code_material.py` 默认每页 50 行；达到 60 页时生成 `代码-前30页.md` 和 `代码-后30页.md`，不足 60 页时生成 `代码-全部.md`。 |
| 用户手册 | 第十条要求软件鉴别材料包括文档鉴别材料；文档一般提交前、后各连续 30 页，不足 60 页时提交全部。 | `generate_manual_draft.py` 生成可作为文档鉴别材料基础的操作手册草稿，结构包含相关文档、说明、功能特点、系统要求、具体操作、常见问题和术语表；正式页数由 Word 排版后复核。 |
| 信息采集表 | 登记申请信息需要由申请人确认，软件名称、版本号、权利人、日期、运行环境等字段应与鉴别材料一致。 | `generate_application_info.py` 只生成草稿并列出待确认字段；`confirm_stage.py --stage application-fields` 在仍有 `待用户确认` 时阻止进入正式生成。 |
| 截图材料 | 截图不是源程序替代物，应来自真实系统页面或用户提供图片，用于支撑用户手册中的操作说明。 | `confirm_stage.py --stage screenshot-method` 先确认截图方式；`capture_screenshots.py` 整理用户截图并生成清单；跳过截图时保留 Word 中可见的截图预留文字。 |
| 三件套一致性 | 软件全称、版本号、源程序量、主要功能和技术特点需要在申请表、手册、源码材料之间保持一致。 | `build_docx_from_md.py` 正式生成前检查业务、代码、截图、申请表和 Markdown 门禁；`review_three_piece_package.py` 复核正式资料目录。 |

源码格式口径：保留正常缩进和必要注释，不通过删除注释、删除空格、压缩或混淆来凑页数；清理尾随空格、连续无意义空行、密钥、账号、客户隐私和无关第三方主体代码。规则说明见 [references/copyright_material_rules.md](references/copyright_material_rules.md) 和 [references/code_selection_rules.md](references/code_selection_rules.md)。

## 自检

发布或提交前运行：

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_skill_package.py
```

自检覆盖：

- skill 结构和 frontmatter。
- `agents/openai.yaml`、README、SKILL 名称一致性。
- `scripts/*.py` 语法。
- 常见密钥形态、个人绝对路径和旧口径残留。

## 发布

初版发布标签为 `v0.1.0`。发布前需要确认：

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_skill_package.py
git status --short
```

变更说明维护在 [CHANGELOG.md](CHANGELOG.md)。GitHub Release notes 应包含当前能力范围、验证命令和已知限制。

## GitHub 工作流

issue 和 PR 使用当前态、自解释格式，正文优先写当前目标、当前范围、当前工作包、当前依赖和验收口径。模板位于 `.github/ISSUE_TEMPLATE/` 和 `.github/PULL_REQUEST_TEMPLATE.md`。

## 目录结构

```text
.
├── .github/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
├── tests/
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 致谢

本项目参考并吸收了开源社区中关于软件著作权申请材料生成、DOCX 文档处理和 agent workflow 设计的实践经验。

## License

MIT
