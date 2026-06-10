# software-copyright-generator

用于生成、整理和复核中国软件著作权登记申请材料的工具集，可作为 Codex / Claude Code skill 安装使用，也可直接以 Python 脚本方式独立运行。

工具以真实项目源码为输入，经过逐阶段人工确认，最终输出软著申请所需的三件套材料：**信息采集表、用户手册、源代码材料**，并对正式产物执行一致性复核。

## 功能特性

- **项目分析**：扫描项目结构、语言构成、入口、路由、页面、组件、接口与源码统计，作为后续材料的事实依据。
- **前置采集**：生成结构化采集表，按登记权属、开发发表、项目形态、业务范围、源码材料、运行截图、模板输出、正式资料检查八个分组收集申请信息，覆盖单体、前后分离、多仓库、移动端、小程序、桌面端等项目形态。
- **业务理解确认**：基于项目证据生成业务理解草稿，行业、目标用户、核心功能与手册章节范围均需申请人确认后方可继续。
- **申请表信息**：按登记字段口径生成信息采集表草稿，标记全部待确认字段；存在历史申请表模板时支持 DOCX 模板套打。
- **源代码材料**：生成候选源码清单（附选择理由与行段标注），经确认后按页数规则分页输出，保留原始行号追溯清单。
- **用户手册**：生成段落化操作手册草稿，采用相关文档、说明、功能特点、系统要求、页面操作、常见问题、术语表的传统结构，并附自检记录。
- **截图管理**：浏览器自动截图前先做就绪检查，提示申请人启动 Web 服务并确认访问地址可达后再采集（自动截图目前仅支持 Web 端服务）；也支持整理申请人提供的截图并生成清单；暂不截图时在正式文档中保留可见的截图预留标识。
- **正式生成与复核**：从已确认的 Markdown 草稿生成正式 Word/TXT 文件，并对三件套执行完整性、一致性、禁用词与 DOCX 结构复核。
- **服务化编排**：提供统一的阶段入口与 JSON manifest 协议，供上层服务按阶段调度。

## 软著材料口径

材料生成遵循《计算机软件著作权登记办法》第十条对软件鉴别材料的要求：

| 材料 | 登记要求 | 工具实现 |
| --- | --- | --- |
| 源程序 | 前、后各连续 30 页；不足 60 页提交全部；每页一般不少于 50 行 | 默认每页 50 行分页；达到 60 页时输出前 30 页与后 30 页，不足 60 页时输出全部；页眉含软件全称与版本号，后 30 页页码从真实起始页继续编号 |
| 文档（用户手册） | 前、后各连续 30 页；不足 60 页提交全部；每页一般不少于 30 行 | 生成符合传统结构的操作手册，正式页数与行数在 Word 排版后复核 |
| 登记信息 | 软件名称、版本号、权利人、日期、环境等字段须与鉴别材料一致 | 草稿阶段标记全部待确认字段，存在未确认字段时阻止正式生成 |
| 材料真实性 | 鉴别材料应来自申请软件本身 | 源代码仅从真实项目源文件抽取；截图仅来自真实系统页面或申请人提供的文件 |
| 三件套一致性 | 软件全称、版本号、主要功能须在各材料间保持一致 | 正式生成前检查全部确认门禁；生成后对正式资料目录执行三件套复核 |

源码材料保留正常缩进与必要注释，不通过删除注释、压缩或混淆凑页数；抽取时自动清理行尾空格、限制连续空行，超宽长行按显示宽度换行计入行数，保证 Word 每页实际行数与分页一致。详细规则见 [references/copyright_material_rules.md](references/copyright_material_rules.md) 与 [references/code_selection_rules.md](references/code_selection_rules.md)。

## 范围与边界

本工具负责生成与复核申请材料，不替代登记流程中的以下环节：

- 正式登记申请表需在中国版权保护中心官网在线填写并签章，本工具输出的信息采集表用于支撑该填写过程。
- 身份证明文件（营业执照、身份证等）与权属证明文件（委托开发合同、合作开发协议等）由申请人自行准备。
- 浏览器自动截图目前仅支持可通过浏览器访问的 Web 端服务；移动端、小程序、桌面端项目的截图由申请人自行提供。
- 软件名称、版本号、著作权人、开发完成日期、发表状态等登记字段的最终确认责任在申请人。
- 本工具不构成法律意见；登记受理与审查结果以登记机构为准。

## 环境要求

| 依赖 | 必需性 | 用途 |
| --- | --- | --- |
| Python 3.10+ | 必需 | 运行全部脚本 |
| python-docx | 可选 | 完整 DOCX 生成、模板套打、正式资料深度复核；缺失时代码材料走基础 OOXML 兜底 |
| Playwright | 可选 | Web 服务页面自动截图（仅支持浏览器可访问的 Web 端服务） |
| pandoc / LibreOffice / Office | 可选 | 本地预览与人工校验 |

## 安装

作为 skill 安装到本地 skill 目录：

```bash
mkdir -p ~/.codex/skills
git clone git@github.com:fanbuz/software-copyright-generator-skill.git ~/.codex/skills/software-copyright-generator
```

安装后重启 Codex 或在新会话中触发，skill 名称为 `software-copyright-generator`，与 [SKILL.md](SKILL.md) frontmatter 一致。

也可不安装为 skill，直接克隆仓库后以脚本方式使用。

## 快速开始

以下命令在待申报项目的根目录执行，`<skill-dir>` 为本仓库所在路径，输出统一写入 `软件著作权申请资料/`。

**1. 生成前置采集表，交申请人填写**

```bash
python3 <skill-dir>/scripts/generate_input_form.py --out 软件著作权申请资料/前置采集表.md
```

申请人提交后记录确认：

```bash
python3 <skill-dir>/scripts/confirm_stage.py --workdir 软件著作权申请资料 --stage preflight --note "已提交前置采集表"
```

**2. 环境检查与项目分析**

```bash
python3 <skill-dir>/scripts/check_environment.py --out-dir 软件著作权申请资料
python3 <skill-dir>/scripts/analyze_project.py --project . --out 软件著作权申请资料/analysis/project.json
```

**3. 业务理解与各项草稿**

```bash
python3 <skill-dir>/scripts/generate_business_context.py --project . \
  --analysis 软件著作权申请资料/analysis/project.json --software-name "<软件全称>"
```

业务理解、申请表字段、代码选择、截图方式、Markdown 草稿均为确认节点，每次确认后执行 `confirm_stage.py` 记录对应阶段。

**4. 正式生成与复核**

```bash
python3 <skill-dir>/scripts/build_docx_from_md.py --workdir 软件著作权申请资料 \
  --software-name "<软件全称>" --version "V1.0"
python3 <skill-dir>/scripts/review_three_piece_package.py --dir 软件著作权申请资料/正式资料 \
  --software-name "<软件全称>" --version "V1.0"
```

正式产物位于 `软件著作权申请资料/正式资料/`，文件按「软件全称-版本号-材料名」命名，例如 `演示系统-V1.0-代码(前30页).docx`。

## 工作流程与确认节点

完整流程为：前置采集 → 环境检查 → 项目定位 → 项目分析 → 业务理解 → 登记字段 → 代码选择 → 草稿生成 → 截图处理 → Markdown 确认 → 正式生成 → 最终复核。

其中以下阶段为强制确认节点，须经申请人确认并通过 `confirm_stage.py` 记录后方可继续：

| 阶段 | 确认内容 |
| --- | --- |
| `preflight` | 软件全称、版本号、著作权人、日期、仓库模式、代码位置等前置信息 |
| `environment` | DOCX 完整环境缺失时的处理方式 |
| `project` | 多候选目录时指定项目目录 |
| `business` | 行业、目标用户、核心功能与申请口径 |
| `application-fields` | 登记字段补全与确认 |
| `code-selection` | 源码抽取文件与行段 |
| `screenshot-method` | 截图方式（自动采集 / 申请人提供 / 暂不截图） |
| `screenshot-ready` | 浏览器自动截图前：申请人启动 Web 服务，确认访问地址可达（仅支持 Web 端服务） |
| `markdown` | 全部草稿确认，准予生成正式文件 |

## 脚本一览

| 脚本 | 用途 |
| --- | --- |
| `scripts/generate_input_form.py` | 生成前置采集表 Markdown 与 JSON 字段契约 |
| `scripts/check_environment.py` | 检查 Markdown/TXT/DOCX 生成能力 |
| `scripts/analyze_project.py` | 项目结构、语言、入口、路由、页面与源码统计 |
| `scripts/generate_business_context.py` | 业务理解证据与确认稿 |
| `scripts/generate_application_info.py` | 申请表信息草稿 |
| `scripts/propose_code_selection.py` | 源码候选清单与选择文件 |
| `scripts/extract_code_material.py` | 代码材料分页与追溯清单 |
| `scripts/generate_manual_draft.py` | 用户手册草稿与自检记录 |
| `scripts/capture_screenshots.py` | 截图采集与清单整理 |
| `scripts/fill_info_form_from_template.py` | 历史申请表 DOCX 模板套打 |
| `scripts/build_docx_from_md.py` | 正式 Word/TXT 生成 |
| `scripts/review_three_piece_package.py` | 三件套正式资料复核 |
| `scripts/confirm_stage.py` | 确认门禁记录 |
| `scripts/run_stage.py` | 服务化阶段统一入口 |

## 服务化调用

上层服务可通过 JSON manifest 按阶段调度：

```bash
python3 scripts/run_stage.py --manifest job.json --stage preflight
python3 scripts/run_stage.py --manifest job.json --stage scan
```

支持 `preflight`、`scan`、`business`、`code-selection`、`draft`、`screenshots`、`build`、`review` 阶段。阶段需要用户输入时返回：

```json
{
  "ok": false,
  "requires_user_input": true,
  "next_action": "business confirmation required"
}
```

退出码：`0` 阶段完成；`10` 等待用户确认；`1` 执行失败；`2` 参数错误。manifest 字段说明见 [references/job_manifest.md](references/job_manifest.md)。

## 目录结构

```text
.
├── SKILL.md                 # skill 元信息与执行规范
├── agents/openai.yaml       # agent 接入元信息
├── references/              # 软著材料规则、手册结构、字段口径、复核清单
├── scripts/                 # 生成、确认、复核脚本
├── tests/                   # 单元测试
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 开发与测试

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_skill_package.py
```

测试覆盖工作流契约、前置采集表与包结构校验；包自检包含 skill 结构、frontmatter、脚本语法与敏感信息残留检查。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢

本项目参考并吸收了开源社区中关于软件著作权申请材料生成、DOCX 文档处理和 agent workflow 设计的实践经验。

## License

[MIT](LICENSE)
