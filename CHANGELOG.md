# Changelog

## Unreleased

- 扩展前置采集表场景字段，覆盖登记权属、开发发表、项目形态、业务手册、源码材料、运行截图、模板输出和正式资料检查。
- 增加前置采集表入口，用户提出生成软著材料时先收集登记信息、仓库模式、代码位置、运行截图和输出配置。
- 增加 `scripts/generate_input_form.py`，支持输出 Markdown 表单和 JSON 字段契约。
- `scripts/run_stage.py` 增加 `preflight` 阶段，服务化调用可在工作目录生成前置采集表并等待用户输入。
- `scripts/confirm_stage.py` 增加 `preflight` 门禁记录。

## v0.1.0

初版发布基线，包含：

- Codex skill 元信息、README、MIT License 和 OpenAI agent 元信息。
- 项目扫描、业务理解证据、申请表草稿、操作手册草稿、代码材料分页、截图整理、DOCX/TXT 生成和三件套复核脚本。
- `scripts/validate_skill_package.py` 仓库自检。
- `scripts/run_stage.py` 服务化阶段入口。
- `references/` 下的软著材料规则、业务理解规则、代码选择规则、手册结构、项目扫描契约、job manifest 协议和最终复核清单。

验证命令：

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_skill_package.py
```

当前限制：

- DOCX 模板套打和最终 DOCX 深度复核需要本机可用 `python-docx`。
- 浏览器自动截图依赖 Playwright；没有登录态或运行中的系统时，应使用用户提供截图或选择暂不截图。
- 本 skill 不替代申请人对软件名称、权利人、日期、发表状态等登记字段的确认。
