# 项目扫描输出契约

`scripts/analyze_project.py` 输出 `analysis.v1`，供业务理解、代码选择和草稿生成阶段读取。

## 关键字段

| 字段 | 说明 |
| --- | --- |
| `schema_version` | 当前固定为 `analysis.v1`。 |
| `project_root` | 被扫描项目的绝对路径，仅用于本次工作目录追溯，不应写入公开样例。 |
| `project_name` | 项目目录名。 |
| `software_name_candidate` | 根据包名或目录名生成的软件名称候选，必须由用户确认后才能进入正式资料。 |
| `package` | `package.json` 名称、版本、脚本和依赖名称。 |
| `frameworks` | 根据依赖和源码后缀识别的框架候选。 |
| `language` | 根据源码后缀统计得到的语言摘要。 |
| `source.file_count` | 纳入候选范围的源码文件数。 |
| `source.line_count` | 源码行数，包含空行。 |
| `source.categorized_files` | 按入口、路由、页面、组件、接口、模型、状态、工具、样式和普通源码分类的相对路径。 |
| `routes` | 从路由文件、页面和链接中提取的路径候选。 |
| `feature_candidates` | 从路由、页面和业务文件名推断的功能候选，只能作为模型研判证据。 |
| `contract` | 说明该输出服务的阶段、稳定字段和排除目录。 |

## 排除规则

扫描默认排除依赖目录、构建产物、覆盖率目录、隐藏目录、输出目录、lock 文件、sourcemap、minified 文件和二进制文件。项目扫描只提供事实证据，不直接决定行业、功能、软件名称或申报字段。

## 验证命令

```bash
python3 scripts/analyze_project.py --project /path/to/demo-project --out 软件著作权申请资料/analysis/project.json
python3 scripts/validate_skill_package.py
```
