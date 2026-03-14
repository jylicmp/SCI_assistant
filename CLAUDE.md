# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SCI_assistant is a literature summarization and synchronization tool for Condensed Matter Physics papers. It uses Claude's subagent system to generate structured markdown summaries from PDFs and syncs them to Notion.

## Core Architecture

### Dual-Runtime Stack
- **Python 3.7+**: Main processing logic, Notion API integration, file watching
- **Node.js 20+**: Markdown to Notion Blocks conversion via `@tryfabric/martian`

### Directory Structure
```
SCI_assistant/
├── data_md/              # Generated literature summaries (HashID.md)
├── input_pdfs/           # Input PDF directory
├── output_pdfs/          # Archived PDFs (renamed to HashID.pdf)
├── .claude/
│   ├── agents/
│   │   └── cmp-summarizer.md   # Subagent prompt template
│   └── skills/
│       ├── cmp-summary-workflow/  # Main workflow skill
│       └── cmp-peer-review/       # Peer review skill
├── notion_sync.py        # Notion synchronization script
├── notion_schema.py      # Database schema definition
├── file_watcher.py       # Watchdog-based file monitor
├── martian_convert.js    # Node.js markdown converter
├── metadata.csv          # Paper metadata lookup table
└── package.json          # Node.js dependencies
```

## Skills & Agents System

### cmp-summary-workflow (`/invoke-cmp-summary-workflow`)
Main workflow for processing PDFs. When user requests summarization:
1. Extract metadata from `metadata.csv` (Author, Journal, Year, Title)
2. Compute SHA256 Hash ID: `sha256([auth1][journal][year][title])` as base-10 integer
3. Archive PDF: `input_pdfs/x.pdf` → `output_pdfs/<HashID>.pdf`
4. Invoke subagent: `claude -p "$(< .claude/agents/cmp_summarizer.md)" > data_md/<HashID>.md`

### cmp_summarizer (Subagent)
Expert CMP physicist subagent. Reads PDFs and outputs structured markdown with:
- Metadata section with Hash ID, Authors, Journal/Year, Keywords
- LaTeX equations in `$$...$$` format
- Structured sections: Motivation, Core Physics, Methods, Results, Limitations

## Notion Sync System

### Workflow
1. **Full sync**: `python notion_sync.py --sync-all`
2. **Single file**: `python notion_sync.py --file data_md/xxx.md`
3. **File watcher**: `python file_watcher.py --background` (auto-sync on changes)

### Key Design
- **Hash ID** serves as unique identifier for incremental updates
- **martian_convert.js** handles Markdown → Notion Blocks conversion (supports GFM, LaTeX)
- **notion_sync.py** parses metadata section and converts to Notion properties

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Full Notion sync
python notion_sync.py --sync-all
python notion_sync.py --sync-all --dry-run  # Preview mode

# Start file watcher (auto-sync on changes)
python file_watcher.py              # Foreground
python file_watcher.py --background # Background
python file_watcher.py --status     # Check status
python file_watcher.py --stop       # Stop watcher

# Test martian converter
echo "# Test" | node martian_convert.js
node martian_convert.js --file input.md
```

## Environment Configuration

`.env` file (required for Notion sync):
```
NOTION_TOKEN=ntn_xxx
NOTION_DATABASE_ID=xxx
```

## Notion Database Schema

| Property | Type | Source |
|----------|------|--------|
| Title | Title | Markdown H1 |
| Hash ID | Text | `File Hash ID` metadata |
| Authors | Text | `Authors` metadata |
| Journal | Text | `Journal/Year` metadata |
| Year | Number | `Journal/Year` metadata |
| Keywords | Multi-select | `Keywords` metadata |
| File Path | Text | Relative file path |
| Last Modified | Date | File mtime |

## Key Implementation Details

1. **Markdown format**: Uses structured metadata section (`## 📄 基本信息`) instead of YAML frontmatter
2. **Block filtering**: Skips metadata blocks, keeps content from numbered sections
3. **Update strategy**: Delete existing blocks → append new blocks (ensures clean updates)
4. **Debounce**: File watcher uses 2-second debounce to avoid rapid triggers
