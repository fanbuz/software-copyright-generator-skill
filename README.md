# Software Copyright Generator Skill

`software-copyright-generator` 是一个用于生成、修复和复核中国软件著作权申请材料的 Codex skill。

它面向真实项目工作流，覆盖：

- 项目分析与业务理解
- 申请表字段确认
- 源代码材料选择与分页
- 用户手册草稿生成
- 截图方式确认与整理
- Word/TXT 正式材料生成
- 信息采集表、用户手册、源代码三件套复核

## 结构

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
├── LICENSE
└── README.md
```

## 使用方式

将本仓库作为 skill 安装到 Codex skill 目录后，在需要处理软著申请资料时调用 `software-copyright-generator`。

本 skill 默认把生成材料写入当前工作目录下的：

```text
软件著作权申请资料/
```

正式输出位于：

```text
软件著作权申请资料/正式资料/
```

## 依赖

- Python 3.10+
- 可选：`python-docx`，用于更完整的 DOCX 生成和模板处理

如果缺少 `python-docx`，部分脚本会走基础 OOXML 兜底路径或提示能力限制。

## 致谢

本项目参考并吸收了开源社区中关于软件著作权申请材料生成、DOCX 文档处理和 agent workflow 设计的实践经验。

## License

MIT
