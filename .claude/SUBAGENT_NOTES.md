# Subagent 使用注意事项

## 概述
`cmp-summarizer` 是 SCI Assistant 的核心子代理，负责读取 PDF 并生成结构化中文摘要。由于子代理输出不稳定，需要特别注意以下事项。

---

## 常见问题

### 1. 开头多余文字
**问题**: 子代理在 `#` 标题前添加介绍性文字
```markdown
我已完成对这篇论文的阅读和总结。以下是生成的文献摘要：

---

# Paper Title - Literature Summary
```

**解决**:
- 删除 `#` 前的所有内容
- 删除 `---` 分隔线

### 2. H2 标题包含英文
**问题**: 子代理在 H2 标题后添加英文括号
```markdown
## 1. 动机与背景 (Motivation & Background)
## 2. 核心创新点 (Key Innovations)
```

**解决**:
- 模板已更新为纯中文标题
- 使用 sed 批量替换：`sed -i '' 's/## 1\. 动机与背景 (Motivation & Background)/## 1. 动机与背景/g'`

### 3. 文件末尾有额外内容
**问题**: 第8节后添加总结段落
```markdown
## 8. 可拓展性与遗留问题
...

---

**总结**: 本工作...
```

**解决**:
- 删除第8节后的所有内容
- 文件必须以 "未解之谜" 内容结尾

### 4. 缺少章节
**问题**: 某些章节内容为空或缺失

**解决**:
- 检查8个必需章节是否都存在
- 如有缺失，使用主代理重新生成

### 5. 语言混用
**问题**: 叙述性内容出现英文

**解决**:
- 在提示中明确要求 "ALL narrative text MUST be in Chinese"
- 仅允许 LaTeX 公式、物理量、关键词使用英文

---

## 最佳实践

### 调用前准备
1. **提取准确的元数据**: 从 metadata.csv 获取作者、期刊、年份
2. **计算正确的 Hash ID**: 使用 `[auth1][journal][year][title]` 格式
3. **检查 PDF 是否已分类**: 确保不是 supplement/review/book

### 调用参数
```bash
claude --agent cmp-summarizer -p "The unique Hash ID for this paper is: <HashID>.

Metadata for this paper:
- Authors: <authors>
- Journal/Year: <journal> / <year>
- Title: <title>

IMPORTANT REQUIREMENTS:
1. **Journal/Year field MUST be filled**
2. **Keywords MUST be in ENGLISH only**
3. **ALL narrative text MUST be in Chinese**
4. **MUST include exactly 8 sections**

Please read and summarize this paper: output_pdfs/<HashID>.pdf" > "data_md/<HashID>.md"
```

### 调用后验证（必须执行）
生成后必须执行 Step 4.5 验证：

```bash
# 检查8个章节
for section in "动机与背景" "核心创新点" "核心物理图像与模型" "方法与技术" "关键结果与证据" "通用性与局限性" "结论与探讨" "可拓展性与遗留问题"; do
    if ! grep -q "$section" "data_md/${hash_id}.md"; then
        echo "Missing: $section"
    fi
done

# 检查文件结尾
tail -3 "data_md/${hash_id}.md"
```

---

## 模板更新记录

### v1.3.1 (2026-03-21)
- H2 标题改为纯中文（去除英文括号）
- 添加 "CRITICAL OUTPUT RULES" 部分
- 明确禁止开头文字、分隔线、额外总结

### v1.3 (2026-03-21)
- 添加中文输出要求
- 添加8章节结构
- 添加格式验证说明

---

## 故障排除

| 症状 | 原因 | 解决方案 |
|------|------|----------|
| 生成内容不完整 | 上下文不足 | 使用主代理重新生成 |
| 格式混乱 | 模板理解错误 | 检查模板版本，更新到最新 |
| 英文过多 | 语言要求不明确 | 在提示中强化中文要求 |
| 缺少公式 | PDF解析问题 | 手动添加关键公式 |
| 章节顺序错误 | 输出格式错误 | 删除并重新生成 |

---

## 重新生成流程

当子代理输出严重错误时：

1. **读取 PDF 内容**
2. **使用主代理生成**（不使用subagent）
3. **按照模板格式手动整理**
4. **验证所有8个章节**
5. **更新 lookup tables**

---

## 环境要求

- Python 3.7+
- Node.js 20+
- Claude CLI 已安装并配置
- 子代理文件: `.claude/agents/cmp-summarizer.md`

---

## 相关文件

- `.claude/agents/cmp-summarizer.md` - 子代理模板
- `.claude/skills/cmp-summary-workflow/SKILL.md` - 工作流定义
- `data_md/` - 生成的摘要目录
- `output_pdfs/` - 归档的PDF目录
