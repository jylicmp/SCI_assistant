# SCI Assistant

文献总结与同步工具，专为凝聚态物理（Condensed Matter Physics）研究领域设计。自动从 PDF 论文生成结构化 Markdown 摘要，并同步到 Notion 知识库。

## 功能特性

- **AI 驱动摘要**：使用 Claude 子代理自动阅读和总结 CMP 领域论文
- **结构化输出**：生成包含动机、核心物理、方法、结果的标准格式摘要
- **Notion 同步**：自动将摘要同步到 Notion 数据库，支持增量更新
- **文件监控**：实时监控目录变化，自动触发同步
- **LaTeX 支持**：完整支持物理公式和数学表达式

## 系统架构

### 双运行时栈
- **Python 3.7+**：主处理逻辑、Notion API 集成、文件监控
- **Node.js 20+**：通过 `@tryfabric/martian` 进行 Markdown 到 Notion Blocks 转换

### 目录结构

```
SCI_assistant/
├── data_md/              # 生成的文献摘要 (HashID.md)
├── input_pdfs/           # 输入 PDF 目录
├── output_pdfs/          # 归档 PDF (重命名为 HashID.pdf)
├── .claude/
│   ├── agents/
│   │   └── cmp-summarizer.md   # 子代理提示模板
│   └── skills/
│       ├── cmp-summary-workflow/  # 主工作流技能
│       └── cmp-peer-review/       # 同行评审技能
├── notion_sync.py        # Notion 同步脚本
├── notion_schema.py      # 数据库模式定义
├── file_watcher.py       # 基于 watchdog 的文件监控器
├── martian_convert.js    # Node.js Markdown 转换器
├── dify_upload.py        # Dify 知识库上传工具
├── metadata.csv          # 论文元数据查找表
└── package.json          # Node.js 依赖
```

## 快速开始

### 1. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# Node.js 依赖
npm install
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# Notion 配置
NOTION_TOKEN=secret_xxx
NOTION_DATABASE_ID=xxx

# Dify 配置（可选）
DIFY_API_KEY=dataset-xxx
DIFY_BASE_URL=http://your-server/v1
DIFY_KNOWLEDGE_BASE_ID=xxx
DOC_DIR=/path/to/your/documents
DOC_SUFFIX=pdf
```

### 3. 使用 Skills

本项目使用 Claude Code Skills 系统：

```bash
# 处理单篇或多篇论文
/invoke-cmp-summary-workflow

# 同行评审
/invoke-cmp-peer-review
```

## 核心工作流

### cmp-summary-workflow

主工作流用于处理 PDF 论文：

1. 从 `metadata.csv` 提取元数据（作者、期刊、年份、标题）
2. 计算 SHA256 Hash ID：`sha256([auth1][journal][year][title])` 转为 10 进制整数
3. 归档 PDF：`input_pdfs/x.pdf` → `output_pdfs/<HashID>.pdf`
4. 调用子代理生成摘要：输出到 `data_md/<HashID>.md`

### cmp_summarizer 子代理

专业凝聚态物理子代理，读取 PDF 并输出结构化 Markdown：

- **元数据部分**：Hash ID、作者、期刊/年份、关键词
- **LaTeX 公式**：使用 `$$...$$` 格式
- **结构化章节**：动机、核心物理、方法、结果、局限性

## Notion 同步系统

### 同步命令

```bash
# 全量同步
python notion_sync.py --sync-all

# 同步单个文件
python notion_sync.py --file data_md/xxx.md

# 预览模式（不实际应用更改）
python notion_sync.py --sync-all --dry-run
```

### 文件监控器

自动监控 `data_md/` 目录变化并同步：

```bash
# 前台运行
python file_watcher.py

# 后台运行
python file_watcher.py --background

# 查看状态
python file_watcher.py --status

# 停止监控
python file_watcher.py --stop
```

### Notion 数据库模式

| 属性 | 类型 | 来源 |
|------|------|------|
| Title | Title | Markdown H1 |
| Hash ID | Text | `File Hash ID` 元数据 |
| Authors | Text | `Authors` 元数据 |
| Journal | Text | `Journal/Year` 元数据 |
| Year | Number | `Journal/Year` 元数据 |
| Keywords | Multi-select | `Keywords` 元数据 |
| File Path | Text | 相对文件路径 |
| Last Modified | Date | 文件修改时间 |

## Dify 集成

上传文献到 Dify 知识库：

```bash
# 上传指定目录的所有文档
python dify_upload.py
```

配置说明：
- `DOC_DIR`：文献目录路径
- `DOC_SUFFIX`：文件后缀（支持多后缀，逗号分隔）
- 自动递归处理子目录

## 测试

```bash
# 测试 martian 转换器
echo "# Test" | node martian_convert.js
node martian_convert.js --file input.md
```

## 关键实现细节

1. **Markdown 格式**：使用结构化元数据部分（`## 📄 基本信息`）而非 YAML frontmatter
2. **Block 过滤**：跳过元数据块，仅保留编号章节的内容
3. **更新策略**：删除现有块 → 添加新块（确保干净更新）
4. **防抖机制**：文件监控器使用 2 秒防抖避免频繁触发

## 环境要求

- Python 3.7+
- Node.js 20+
- macOS / Linux / Windows

## 许可证

ISC

## 相关链接

- [GitHub Repository](https://github.com/jylicmp/SCI_assistant)
- [Martian](https://github.com/tryfabric/martian) - Markdown to Notion 转换工具
- [Notion API 文档](https://developers.notion.com/)
- [Claude Code 文档](https://claude.ai/code)
