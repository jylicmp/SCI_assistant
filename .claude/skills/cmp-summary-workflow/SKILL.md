---
name: cmp-summary-workflow
description: "Delegates the task of reading and summarizing one or MORE Condensed Matter Physics (CMP) papers. Handles batch processing (one by one), metadata extraction, SHA256 base-10 renaming, PDF archiving, and native Subagent delegation."
allowed-tools: [Bash, Read, Write]
---

# CMP Literature Summary Workflow & Native Subagent Invoker (Batch Processing Supported)

## Overview
Do NOT summarize Condensed Matter Physics (CMP) papers directly in the main conversation context. If the user requests to summarize multiple papers or an entire directory, you MUST process them **sequentially (one by one)**.

For **EACH** paper, perform a strict preprocessing workflow (Extract Metadata → Compute SHA256 Hash → Rename & Archive PDF) and then perform **Two-Phase Summary Generation**:
1. **Phase 1**: Delegate information extraction to the native `cmp-extractor` Subagent
2. **Phase 2**: Format the extracted information into the standard 8-section Chinese template using the main agent

This two-phase approach achieves higher reliability by separating information extraction (complex cognitive task) from formatting (structured task).

## Execution Workflow (STRICT ORDER)

When the user asks to summarize one or more papers (e.g., "Summarize all PDFs in `input_pdfs/`" or "Summarize A.pdf and B.pdf"):

### Step 0: Identify Target Files
Identify the exact paths of all PDF files the user wants to process. If a directory is specified, use the `Bash` tool to list all `.pdf` files inside it.

### Step 0.0: Check Processed Papers Lookup Table (CRITICAL - Run FIRST)
**Before processing any PDF, first check the `processed_papers.csv` and `working_papers.csv` lookup tables** to determine if a paper has already been processed or is currently being processed.

The lookup tables are located at:
- `.claude/skills/cmp-summary-workflow/processed_papers.csv` - Completed papers
- `.claude/skills/cmp-summary-workflow/working_papers.csv` - Papers currently being processed (intermediate state)

**Check Process:**
1. Read `processed_papers.csv` to get all already-processed PDF filenames and their Hash IDs
2. Read `working_papers.csv` to get all papers currently being processed
3. For each target PDF, check if its filename exists in either lookup table
4. If found in `processed_papers.csv`, **skip all processing steps** for this file and log it as "Already processed"
5. If found in `working_papers.csv`, **skip all processing steps** for this file and log it as "Currently being processed (in working_papers.csv)"
6. Only create a queue of files that are NOT in either lookup table

**Example lookup table format:**

`processed_papers.csv`:
```
PDF 文件名，HashID
Zhu 等 - 2025 - Magnetic geometry.pdf,99601758296340919977837740649730029451531977553314166620560899200507929180592
Zyuzin - 2025 - Antitoroidal magnets.pdf,22684547456475760315941586172644602821616411693201862336120404181001184982630
```

`working_papers.csv`:
```
PDF 文件名，HashID
Wang 等 - 2024 - In progress paper.pdf,12345678901234567890123456789012345678901234567890123456789012345678
```

**Action:**
- If a PDF is found in `processed_papers.csv`, skip it and move to the next file
- If a PDF is found in `working_papers.csv`, skip it and move to the next file (already being processed)
- Only process PDFs that are NOT in either lookup table (these are unsummarized papers)

**Create a queue of unsummarized files. Process the queue ONE BY ONE by executing Steps 0.1 to 5 for each file before moving to the next.**

### Step 0.1: PDF Classification (CRITICAL - Run BEFORE summarization)
Before processing each PDF, **first classify it** to determine if it should be summarized or moved to a special directory.

**Classification Rules (check in this order):**

#### A. Check for Supplement Material (Highest Priority)
Check if the **filename** contains any of these keywords (case-insensitive):
- `supplementary`, `supplement`, `SI_support`, `supporting`, `supplemental`, `additional`, `MOESM`, `ESI`

**Note:** Use word boundaries carefully. "SI" should only match as a standalone word (e.g., "SI.pdf", "Main_Text_SI.pdf"), not as part of other words (e.g., "Solid", "Site").

**Action if matched:**
```bash
mkdir -p input_supp
mv "path/to/current_paper.pdf" "input_supp/"
```
Skip all remaining steps for this file. Log: "Classified as Supplemental Material -> moved to input_supp/"

#### B. Check for Review Article
Check if **ANY** of these conditions are true:
- metadata contains "Review" in `Item Type` or `Title` fields
- Journal is "Reviews of Modern Physics", "Nature Reviews", "Physics Reports", or similar review journal (e.g., contains "Reviews" in name)
- File size > 5MB **AND** number of pages > 20

To check file size and page count:
```bash
# Check file size in MB
file_size_mb=$(stat -f%z "path/to/file.pdf" 2>/dev/null || stat -c%s "path/to/file.pdf" 2>/dev/null)
file_size_mb=$((file_size_mb / 1048576))

# Check page count (use PyPDF2 if pdfinfo not available)
python3 -c "import PyPDF2; pdf=PyPDF2.PdfReader(open('path/to/file.pdf','rb')); print(len(pdf.pages))"
```

**Action if matched:**
```bash
mkdir -p input_review
mv "path/to/current_paper.pdf" "input_review/"
```
Skip all remaining steps for this file. Log: "Classified as Review Article -> moved to input_review/"

#### C. Check for Book
Check if **ALL** of these conditions are true:
- File size > 10MB
- metadata has `Publisher` field but NO `Journal` or `Publication Title` field

**Action if matched:**
```bash
mkdir -p input_book
mv "path/to/current_paper.pdf" "input_book/"
```
Skip all remaining steps for this file. Log: "Classified as Book -> moved to input_book/"

#### D. Regular Paper (Default)
If none of the above conditions match, classify as **Regular Paper** and proceed with Steps 1-4 for summarization.

### Step 1: Query Metadata (For current file)
Read the `metadata.csv` file. **Use Column 38 "File Attachments" to match the PDF filename** (this provides 100% match rate).

**Metadata Matching Method (Column 38 - File Attachments):**
```python
import csv
import os

pdf_filename = "Zhu 等 - 2024 - Example paper.pdf"
metadata_path = "metadata.csv"

with open(metadata_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)  # Skip header

    for row in reader:
        if len(row) > 37:
            file_attachments = row[37]  # Column 38 (0-indexed: 37)
            # Check if PDF filename is in the File Attachments column
            if pdf_filename in file_attachments:
                # Found matching metadata!
                author = row[3] if len(row) > 3 else ''       # Column 4: Author
                title = row[4] if len(row) > 4 else ''        # Column 5: Title
                journal = row[5] if len(row) > 5 else ''      # Column 6: Publication Title
                year = row[2] if len(row) > 2 else ''         # Column 3: Publication Year
                item_type = row[1] if len(row) > 1 else ''    # Column 2: Item Type
                publisher = row[26] if len(row) > 26 else ''  # Column 27: Publisher
                break
```

**Why Column 38?** The "File Attachments" column contains full paths like:
`/Users/lijiayu/Zotero/storage/ABC12345/Zhu 等 - 2024 - Paper Title.pdf`

This allows exact filename matching, achieving **100% match rate** (tested on 16 PDFs).

Extract the following exact fields:
- `Author` (Extract ONLY the first author's name, format as "FirstLast", e.g., "Zhu, Haiyuan" becomes "HaiyuanZhu")
- `Publication Title` or `Journal Abbreviation` (e.g., "NatureCommunications")
- `Publication Year` (e.g., "2025")
- `Title` (e.g., "Magnetic geometry induced quantum geometry and nonlinear transports")
- `Publisher` (if available, for book classification)
- `Item Type` (if available, for review classification)

**arXiv Preprint Detection:**
After extracting metadata, check if the paper is an arXiv preprint:
```python
# Detect arXiv preprint
is_arxiv = False
if journal and 'arxiv' in journal.lower():
    is_arxiv = True
    journal = 'arXiv'
elif pdf_filename.lower().find('arxiv') != -1:
    is_arxiv = True
    journal = 'arXiv'
```
If `is_arxiv` is True, use "arXiv" as the journal name for subsequent steps.

### Step 2: Construct String & Compute Hash (For current file)
Construct the string `[auth1][journal][year][title]`. **Remove ALL spaces and punctuation** (keep only alphanumeric characters).
Use the `Bash` tool to run the following Python snippet to compute the base-10 integer of the SHA256 hash:

```python
import hashlib, re
raw_str = "HaiyuanZhuNatureCommunications2025Magneticgeometryinducedquantumgeometryandnonlineartransports" # Replace with actual extracted data
clean_str = re.sub(r'[^a-zA-Z0-9]', '', raw_str)
hash_id = int(hashlib.sha256(clean_str.encode('utf-8')).hexdigest(), 16)
print(hash_id)
```
*Capture the printed `<HashID>`.*

**After computing the HashID, immediately append to `working_papers.csv`:**

```python
# Append to working_papers.csv (intermediate state tracking)
with open('.claude/skills/cmp-summary-workflow/working_papers.csv', 'a') as f:
    f.write(f"{pdf_filename},{hash_id}\n")
```

The `working_papers.csv` file tracks papers currently being processed. It serves as a "lock" to prevent duplicate processing if the workflow is interrupted and restarted.

### Step 3: Archive and Rename PDF (For current file)
Ensure the `output_pdfs/` and `data_md/` directories exist.
Use the `Bash` tool to copy the current original PDF to `output_pdfs/`, renaming it with the generated Hash integer.

**Note:** If the PDF was classified in Step 0.1 and moved to a special directory (`input_review/`, `input_book/`, or `input_supp/`), skip this step and Step 4. Only proceed with archiving for **Regular Papers**.

```bash
mkdir -p output_pdfs data_md
cp "path/to/current_paper.pdf" "output_pdfs/<HashID>.pdf"
```
*(Note: Adjust the source path if the file was moved during classification)*

### Step 4: Two-Phase Summary Generation (NEW)

The summary generation is split into two phases to improve reliability and format compliance.

#### Phase 1: Extract Structured Information (Subagent)

Use the `Bash` tool to invoke the `cmp-extractor` subagent to read the PDF and extract all key information in structured English format:

```bash
claude --bare --agent cmp-extractor -p "Please read and extract structured information from this paper:

output_pdfs/<HashID>.pdf

The Hash ID for this paper is: <HashID>

Extract all sections (METADATA, RESEARCH_QUESTION, KEY_INNOVATIONS, CORE_PHYSICS, METHODS, RESULTS, LIMITATIONS, CONCLUSIONS) in detail." 2>&1
```

**Why this approach?**
- The `cmp-extractor` subagent has a simpler task: just extract information, no formatting constraints
- High success rate for information extraction
- Captures Hamiltonians, equations, parameters, and physical mechanisms accurately

#### Phase 2: Format to Standard Template (Main Agent)

After receiving the extracted information from Phase 1, use the `Write` tool to create the final summary following the strict 8-section Chinese template format.

**Template Structure:**
```markdown
# [Paper Title] - Literature Summary

## 📄 基本信息
- **Authors**: [from extracted metadata]
- **Journal/Year**: [from extracted metadata]
- **File Hash ID**: [HashID]
- **Keywords**: [3-5 English keywords from extraction]

## 🎯 一句话摘要
> [1-2 sentence summary in Chinese]

## 1. 动机与背景
- **研究空白**: [from RESEARCH_QUESTION]
- **研究目的**: [from RESEARCH_QUESTION]

## 2. 核心创新点
- [from KEY_INNOVATIONS]

## 3. 核心物理图像与模型
- **物理机制**: [from CORE_PHYSICS]
- **核心方程**: [LaTeX equations from CORE_PHYSICS]
- **物理假设**: [from CORE_PHYSICS]

## 4. 方法与技术
- **实验细节**: [from METHODS]
- **理论/计算细节**: [from METHODS]

## 5. 关键结果与证据
- **决定性证据**: [from RESULTS]
- **主要发现**: [from RESULTS]

## 6. 通用性与局限性
- **通用性**: [from LIMITATIONS]
- **局限性**: [from LIMITATIONS]

## 7. 结论与探讨
- [from CONCLUSIONS]

## 8. 可拓展性与遗留问题
- **未来方向**: [from CONCLUSIONS - Future directions]
  - [List 3-4 items]
- **未解之谜**: [from CONCLUSIONS - Open questions]
  - [List 3-4 items]
```

**Formatting Rules:**
1. ALL narrative text must be in **Chinese (中文)**
2. Only these elements can be in English:
   - LaTeX equations and mathematical symbols
   - Physical quantities (temperatures, fields, etc.)
   - Material names, software names, institution names
   - Keywords (in the metadata section)
3. Section headers must be pure Chinese (NO English in parentheses)
4. File must start immediately with `# [Title]` (no intro text)
5. File must end after Section 8 "未解之谜" (no final summary)
6. Do NOT use `---` separator lines anywhere

Save the formatted summary to: `data_md/<HashID>.md`

### Step 4.5: Validate Summary Format (CRITICAL)
After Phase 2 formatting is complete, **verify the generated summary strictly follows the template format**. Read the generated file and check for compliance.

**Validation Checklist:**
1. **Title**: Must be `# [Paper Title] - Literature Summary`
2. **Metadata Section**: Must contain `## 📄 基本信息` with Authors, Journal/Year, File Hash ID, Keywords
3. **Keywords**: Must be in ENGLISH only (no Chinese characters)
4. **Journal/Year**: Must be filled in format 'Journal Name / Year'
5. **8 Required Sections** (Chinese headers only, NO English in parentheses):
   - `## 🎯 一句话摘要`
   - `## 1. 动机与背景`
   - `## 2. 核心创新点`
   - `## 3. 核心物理图像与模型`
   - `## 4. 方法与技术`
   - `## 5. 关键结果与证据`
   - `## 6. 通用性与局限性`
   - `## 7. 结论与探讨`
   - `## 8. 可拓展性与遗留问题`
6. **No Extra Sections**: Must NOT have any content after Section 8 (no final summary block)
7. **Language**: All narrative text must be in Chinese (中文), only equations/keywords in English
8. **Equations**: LaTeX equations should be properly formatted with `$...$` or `$$...$$`

**If Validation Fails:**

Since Phase 2 is performed by the main agent (you), formatting errors should be rare. If they occur:

1. **Missing Content**: If the cmp-extractor output was incomplete, you may need to regenerate the summary with additional prompts
2. **Format Issues**: Use the `Edit` tool to fix specific formatting problems
3. **Language Issues**: Ensure all narrative text is translated to Chinese

**Regeneration Procedure (if extraction was poor):**
- Re-run Phase 1 with the cmp-extractor subagent
- Ensure the extraction captures all required sections
- Re-run Phase 2 formatting

**If Validation Passes:** Proceed to Step 5.

### Step 5: Batch Completion & Final Output and Update Lookup Table
Once ALL papers in the queue have been successfully processed, verify the results.

**For Regular Papers:** Verify that the corresponding `.md` files exist in the `data_md/` directory.

**For Classified Files:** Verify that files were moved to the correct directories (`input_review/`, `input_book/`, `input_supp/`).

**Update the processed_papers.csv lookup table:**
For each successfully processed paper, append a new row to `processed_papers.csv` with the PDF filename and its Hash ID:
```python
# Append to processed_papers.csv
with open('.claude/skills/cmp-summary-workflow/processed_papers.csv', 'a') as f:
    f.write(f"{pdf_filename},{hash_id}\n")
```

**Remove the corresponding entry from working_papers.csv:**
After successfully updating `processed_papers.csv`, remove the entry from `working_papers.csv` to indicate the paper has been fully processed:
```python
# Remove from working_papers.csv (mark as completed)
import csv
working_papers_path = '.claude/skills/cmp-summary-workflow/working_papers.csv'
with open(working_papers_path, 'r', encoding='utf-8') as f:
    lines = [line for line in f if not line.strip().startswith(f"{pdf_filename},")]
with open(working_papers_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
```

Present a comprehensive summary to the user detailing the batch results. For example:
"Successfully processed 5 files:

**Regular Papers (summarized):**
1. `Zhu2025.pdf` -> Archived as `<HashID_1>.pdf`, summary saved to `data_md/<HashID_1>.md`
2. `Wang2023.pdf` -> Archived as `<HashID_2>.pdf`, summary saved to `data_md/<HashID_2>.md`

**Classified Files (not summarized):**
3. `ReviewArticle2024.pdf` -> Classified as Review -> moved to `input_review/`
4. `BookChapter2022.pdf` -> Classified as Book -> moved to `input_book/`
5. `Supplementary_SI.pdf` -> Classified as Supplement -> moved to `input_supp/`

**Already processed (skipped):**
6. `PreviousPaper2024.pdf` -> Found in processed_papers.csv, skipped"

**CRITICAL RULE: DO NOT print the actual markdown summaries in the main chat window. Only report the file paths, Hash IDs, and classification results.**

---

## Subagent Reference

### `cmp-extractor` (Primary - Phase 1)
**Purpose**: Extract structured information from PDF without formatting constraints
**File**: `.claude/agents/cmp-extractor.md`

This subagent reads the PDF and extracts:
- METADATA (Title, Authors, Journal, Year)
- RESEARCH_QUESTION
- KEY_INNOVATIONS
- CORE_PHYSICS (mechanisms, equations, Hamiltonian)
- METHODS (experimental/computational details)
- RESULTS (key findings, evidence)
- LIMITATIONS
- CONCLUSIONS (future directions, open questions)

**Advantages**:
- High success rate for information extraction
- No formatting constraints (simpler task)
- Captures detailed technical content

### `cmp-summarizer` (Legacy - Optional)
**Purpose**: Directly generate formatted summary (original approach)
**File**: `.claude/agents/cmp-summarizer.md`


**Use only if**:
- The two-phase approach fails for a specific paper
- User explicitly requests single-phase summarization
- cmp-extractor is unavailable

**Note**: This subagent often struggles with strict format compliance and language switching.

---

## Notion Sync Subagent (`notion-sync`)

For syncing local summaries to Notion database, use the dedicated `notion-sync` subagent.

### Workflow

The `notion-sync` subagent will:
1. Run `check_sync_status.py` to compare local files vs Notion
2. Identify files that exist only locally (need to be uploaded)
3. Upload each new file using `notion_sync.py --file <path>`
4. Re-run check to verify synchronization
5. Report the sync results

### Usage

```bash
claude --agent notion-sync -p "Sync all local summaries to Notion"
```

Or for specific file:
```bash
claude --agent notion-sync -p "Check sync status and upload HashID: <hash_id>"
```

### Expected Output

- Initial comparison (local vs Notion counts)
- Upload progress for new files
- Final verification confirming sync completion
- Summary of synced files