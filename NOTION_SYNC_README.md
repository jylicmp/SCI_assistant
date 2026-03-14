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
