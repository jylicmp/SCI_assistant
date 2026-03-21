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
├── input_review/         # Classified review articles (not summarized)
├── input_book/           # Classified books (not summarized)
├── input_supp/           # Classified supplementary materials
├── output_pdfs/          # Archived PDFs (renamed to HashID.pdf)
├── .claude/
│   ├── agents/
│   │   └── cmp-summarizer.md   # Subagent prompt template
│   └── skills/
│       ├── cmp-summary-workflow/  # Main workflow skill
│       │   ├── SKILL.md           # Skill definition & workflow
│       │   ├── processed_papers.csv  # Lookup table: completed papers
│       │   └── working_papers.csv    # Lookup table: in-progress papers
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
Main workflow for processing PDFs with batch support and automatic classification:

1. **Check Lookup Tables**: Query `processed_papers.csv` and `working_papers.csv` to skip duplicates
2. **PDF Classification** (v1.1+): Auto-sort into categories:
   - **Supplementary Material**: Files with `supplementary`, `SI`, `supporting` in filename → `input_supp/`
   - **Review Articles**: Metadata indicates review OR file >5MB with >20 pages → `input_review/`
   - **Books**: File >10MB with Publisher but no Journal → `input_book/`
   - **Regular Papers**: Proceed to summarization
3. **Extract Metadata**: From `metadata.csv` Column 38 (File Attachments) for 100% match rate
4. **arXiv Detection** (v1.2+): Detect preprints from journal field or filename
5. **Compute SHA256 Hash ID**: `sha256([auth1][journal][year][title])` as base-10 integer
6. **Archive PDF**: `input_pdfs/x.pdf` → `output_pdfs/<HashID>.pdf`
7. **Invoke Subagent**: Delegate summarization to `cmp-summarizer`
8. **Validate Format** (v1.3+): Check summary follows template (8 sections, Chinese text, no extra content)
9. **Update Lookup Tables**: Mark as processed in `processed_papers.csv`

**Sequential Processing**: When batch processing multiple PDFs, each file is processed one-by-one (not parallel) to prevent context overflow.

### cmp_summarizer (Subagent)
Expert CMP physicist subagent. Reads PDFs and outputs structured markdown with:
- Metadata section with Hash ID, Authors, Journal/Year, Keywords
- LaTeX equations in `$$...$$` format
- Structured sections: Motivation, Core Physics, Methods, Results, Limitations

### notion-sync (Subagent)
Automated sync assistant for Notion integration:
- Checks sync status between local summaries and Notion database
- Uploads new summaries automatically
- Verifies upload results and reports discrepancies

**Usage:**
```bash
# Sync all local summaries to Notion
claude --agent notion-sync -p "Sync all local summaries to Notion"

# Sync specific file
claude --agent notion-sync -p "Check sync status and upload HashID: <hash_id>"
```

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
5. **Lookup Tables**: Prevent duplicate processing and enable resume after interruption
   - `processed_papers.csv`: Tracks completed papers (PDF filename, Hash ID)
   - `working_papers.csv`: Tracks papers currently being processed (lock mechanism)
6. **PDF Classification**: Reduces noise by filtering out supplements, reviews, and books before summarization

---

## Version History

### v1.3.2 (Current)
- **Feature**: Notion sync subagent (`notion-sync`)
  - Automated sync status checking between local and Notion
  - Upload new summaries to Notion database
  - Verify upload results and report discrepancies
- **Fix**: Enhanced subagent template with explicit format rules
  - Added "CRITICAL OUTPUT RULES" section
  - Explicitly forbid intro text, separator lines, extra sections
  - Provide correct/incorrect ending examples

### v1.3
- **Feature**: Automatic summary format validation
  - Check 8 required sections are present
  - Verify Chinese language compliance
  - Ensure no extra content after Section 8
  - Validate metadata format for Notion sync

### v1.2
- **Feature**: arXiv preprint detection
- **Fix**: Subagent invocation using `--agent` flag
- **Improvement**: Better metadata extraction for preprints

### v1.1
- **Feature**: PDF classification system
  - Auto-sort supplementary materials to `input_supp/`
  - Auto-sort review articles to `input_review/`
  - Auto-sort books to `input_book/`
- **Feature**: Lookup table system (`processed_papers.csv`, `working_papers.csv`)
- **Improvement**: Batch processing with sequential execution

### v1.0
- **Feature**: Initial workflow with metadata extraction
- **Feature**: SHA256-based Hash ID generation
- **Feature**: Notion synchronization
- **Feature**: File watcher for auto-sync
