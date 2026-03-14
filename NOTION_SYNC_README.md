# Notion Sync - 文献总结自动同步工具

将 `data_md/` 目录下的文献总结 markdown 文件自动同步到 Notion Database，支持增量更新。

## 功能特性

- **自动检测**: 监听 `data_md/` 文件夹的文件变化（新增、修改）
- **增量同步**: 基于 Hash ID 作为唯一标识，避免重复创建
- **元数据映射**: 自动提取 markdown 中的元数据到 Notion Database 属性
- **内容转换**: 将 markdown 格式转换为 Notion Blocks API 格式

## 前置准备

### 1. 创建 Notion Integration

1. 访问 https://www.notion.so/my-integrations
2. 点击 "+ New integration"
3. 填写名称（如 "Literature Sync"）
4. 选择关联的 Workspace
5. 点击 "Submit"
6. 复制 **Internal Integration Token**（格式：`secret_xxx`）

### 2. 创建 Notion Database

1. 在 Notion 中创建新的 Database（建议使用 Table View）
2. 添加以下列（Properties）：

| 列名 | 类型 | 说明 |
|------|------|------|
| Title | Title | 论文标题（默认列） |
| Hash ID | Text | 唯一标识符 |
| Authors | Text | 作者列表 |
| Journal | Text | 期刊名称 |
| Year | Number | 发表年份 |
| Keywords | Multi-select | 关键词 |
| File Path | Text | 文件路径 |
| Last Modified | Date | 最后修改时间 |

### 3. 共享 Database 给 Integration

1. 打开创建好的 Database
2. 点击右上角 "···" → "Connect to"
3. 选择刚才创建的 Integration
4. 复制 Database ID（URL 中 `/d/` 后面的部分）

### 4. 配置环境变量

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入你的配置：
   ```
   NOTION_TOKEN=secret_xxx
   NOTION_DATABASE_ID=xxx
   ```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 全量同步

将所有 markdown 文件同步到 Notion：

```bash
python notion_sync.py --sync-all
```

### 同步单个文件

```bash
python notion_sync.py --file data_md/xxx.md
```

### 预览模式（Dry Run）

预览同步结果但不实际执行：

```bash
python notion_sync.py --sync-all --dry-run
```

### 启动文件监听器

前台运行（按 Ctrl+C 停止）：

```bash
python file_watcher.py
```

后台运行：

```bash
python file_watcher.py --background
```

停止后台运行：

```bash
python file_watcher.py --stop
```

查看状态：

```bash
python file_watcher.py --status
```

## 文件结构

```
SCI_assistant/
├── notion_sync.py       # 主同步脚本
├── notion_schema.py     # Database Schema 定义
├── file_watcher.py      # 文件监听器
├── .env                 # 环境变量配置（需自行创建）
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
├── data_md/             # 源文件目录
│   ├── xxx.md
│   └── yyy.md
└── file_watcher.log     # 监听器日志
```

## 元数据提取规则

脚本会从 markdown 文件的 "📄 基本信息 (Metadata)" 部分自动提取：

```markdown
## 📄 基本信息 (Metadata)
- **Authors**: 作者列表
- **Journal/Year**: 期刊名 / 年份
- **File Hash ID**: 123456789
- **Keywords**: 关键词 1, 关键词 2, ...
```

提取的元数据将映射到 Notion Database 的对应属性。

## Markdown 转换规则

| Markdown | Notion Block |
|----------|--------------|
| `# Heading` | Heading 1 |
| `## Heading` | Heading 2 |
| `### Heading` | Heading 3 |
| `**bold**` | Bold text |
| `*italic*` | Italic text |
| `$math$` | Code format |
| `- item` | Bulleted list |
| `1. item` | Numbered list |
| `> quote` | Quote |
| `---` | Divider |

## 日志查看

文件监听器日志：

```bash
tail -f file_watcher.log
```

## 故障排查

### 1. 提示 "NOTION_TOKEN and NOTION_DATABASE_ID must be set"

- 检查 `.env` 文件是否存在
- 检查 `.env` 中的配置是否正确

### 2. 同步失败 "Could not find database"

- 检查 Database ID 是否正确
- 确认 Database 已共享给 Integration

### 3. 文件监听器无响应

- 检查 `data_md/` 目录是否存在
- 查看 `file_watcher.log` 了解详细错误

### 4. 重复创建页面

- 检查 markdown 文件中的 Hash ID 是否唯一
- Hash ID 会作为唯一标识符用于判断是否需要更新

## 注意事项

1. **API 限流**: Notion API 有限制，大量文件同步时可能需要等待
2. **Block 数量限制**: 每次请求最多 100 个 blocks，超长内容会被截断
3. **更新行为**: 更新页面时会追加新的 blocks，不会删除原有内容
4. **网络要求**: 需要能够访问 Notion API（api.notion.com）

## 扩展开发

### 添加新的元数据字段

1. 在 `notion_schema.py` 的 `NOTION_SCHEMA` 中添加新字段定义
2. 在 `notion_sync.py` 的 `parse_md_frontmatter()` 中添加解析逻辑
3. 在 Notion Database 中添加对应的列

### 自定义 Block 转换

修改 `notion_sync.py` 中的 `md_to_notion_blocks()` 方法，添加新的 markdown 语法支持。

## 版本历史

### v1.2 (2026-03-14) - arXiv 预印本检测 + Subagent 调用修复

**新增功能：**
- 🆕 **arXiv 预印本自动检测**：当论文为预印本时，Journal/Year 字段自动填入 "arXiv / Year"
  - 检测优先级：元数据期刊字段 → 文件名关键词 → PDF 内容识别
  - 已发表论文仍使用实际期刊名（如 "Physical Review B / 2023"）
  - 仅在无法确定时使用 "Unknown / Year" 作为后备

**Bug 修复：**
- 🐛 **修复 Subagent 调用失败问题**：SKILL.md 中 `claude -p "$(< .claude/agents/cmp_summarizer.md)..."` 语法错误
  - 根本原因：`$()` 命令替换在双引号内破坏换行符，长字符串导致 bash 解析失败
  - 解决方案：改用 `--agent cmp-summarizer` 参数加载 agent 文件
  - 修改文件：`.claude/skills/cmp-summary-workflow/SKILL.md` Step 4

**技术变更：**
- 更新 `cmp-summarizer.md` METADATA RULES：添加 arXiv 预印本优先规则
- 更新 `SKILL.md` Step 1：添加 arXiv 检测逻辑 (`is_arxiv` 标志)
- 更新 `SKILL.md` Step 4：修正 subagent 调用命令格式

**检测规则：**
```python
# arXiv 预print 检测逻辑
is_arxiv = False
if journal and 'arxiv' in journal.lower():
    is_arxiv = True
    journal = 'arXiv'
elif pdf_filename.lower().find('arxiv') != -1:
    is_arxiv = True
    journal = 'arXiv'
```

**输出示例：**
| 论文类型 | Journal/Year 输出 |
|----------|------------------|
| 已发表 | `Physical Review B / 2023` |
| arXiv 预印本 | `arXiv / 2023` |
| 未知来源 | `Unknown / 2023` (后备) |

### v1.1 (2026-03-14) - PDF 自动分类功能

**新增功能：**
- 🆕 **PDF 自动分类**：在总结前自动识别并分类 4 种类型的 PDF
  - 📎 **Supplement (补充材料)**：通过文件名关键词检测 (MOESM, SI, supplementary 等) → `input_supp/`
  - 📚 **书籍 (Book)**：大文件 (>10MB) + 有出版社但无期刊信息 → `input_book/`
  - 📖 **综述 (Review)**：综述期刊 或 大文件 (>5MB, >20 页) → `input_review/`
  - 📄 **普通论文**：不符合以上条件，正常总结流程 → `output_pdfs/` + `data_md/`

**技术变更：**
- 新增 `cmp-summary-workflow` Skill 的 Step 0.1 分类逻辑
- 添加 PyPDF2 依赖用于页数检测
- 新增目录：`input_review/`, `input_book/`, `input_supp/`

**测试验证：**
| 测试文件 | 分类结果 | 目标目录 |
|----------|----------|----------|
| 41467_2017_133_MOESM1_ESM.pdf | Supplement | input_supp/ |
| Ashcroft & Mermin - Solid state physics.pdf | Book (97MB, 848 页) | input_book/ |
| Žutić et al. - Spintronics Review | Review (Rev. Mod. Phys.) | input_review/ |
| Zyuzin - Antitoroidal magnets | Regular Paper | 已总结并同步到 Notion |

### v1.0 (2026-03-13) - 初始版本

**核心功能：**
- Notion 自动同步脚本 (`notion_sync.py`)
- 文件监控器 (`file_watcher.py`)
- 支持全量同步、单文件同步、预览模式
- 基于 Hash ID 的增量更新机制
- Markdown 到 Notion Blocks 转换（支持 LaTeX 公式）
