---
name: cmp-summary-workflow
description: "Delegates the task of reading and summarizing one or MORE Condensed Matter Physics (CMP) papers. Handles batch processing (one by one), metadata extraction, SHA256 base-10 renaming, PDF archiving, and native Subagent delegation."
allowed-tools: [Bash, Read, Write]
---

# CMP Literature Summary Workflow & Native Subagent Invoker (Batch Processing Supported)

## Overview
Do NOT summarize Condensed Matter Physics (CMP) papers directly in the main conversation context. If the user requests to summarize multiple papers or an entire directory, you MUST process them **sequentially (one by one)**. 

For **EACH** paper, perform a strict preprocessing workflow (Extract Metadata -> Compute SHA256 Hash -> Rename & Archive PDF) and then delegate the summarization to the native `cmp_summarizer` Subagent.

## Execution Workflow (STRICT ORDER)

When the user asks to summarize one or more papers (e.g., "Summarize all PDFs in `input_pdfs/`" or "Summarize A.pdf and B.pdf"):

### Step 0: Identify Target Files
Identify the exact paths of all PDF files the user wants to process. If a directory is specified, use the `Bash` tool to list all `.pdf` files inside it.
Create a queue of these files. **Process the queue ONE BY ONE by executing Steps 0.1 to 4 for each file before moving to the next.**

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
Read the `metadata.csv` file. Find the row corresponding to the requested paper (match by title, file name, or author).
Extract the following exact fields:
- `Author` (Extract ONLY the first author's name, format as FirstLast, e.g., "Zhu, Haiyuan" becomes "HaiyuanZhu")
- `Publication Title` or `Journal Abbreviation` (e.g., "NatureCommunications")
- `Publication Year` (e.g., "2025")
- `Title` (e.g., "Magnetic geometry induced quantum geometry and nonlinear transports")
- `Publisher` (if available, for book classification)
- `Item Type` (if available, for review classification)

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

### Step 3: Archive and Rename PDF (For current file)
Ensure the `output_pdfs/` and `data_md/` directories exist.
Use the `Bash` tool to copy the current original PDF to `output_pdfs/`, renaming it with the generated Hash integer.

**Note:** If the PDF was classified in Step 0.1 and moved to a special directory (`input_review/`, `input_book/`, or `input_supp/`), skip this step and Step 4. Only proceed with archiving for **Regular Papers**.

```bash
mkdir -p output_pdfs data_md
cp "path/to/current_paper.pdf" "output_pdfs/<HashID>.pdf"
```
*(Note: Adjust the source path if the file was moved during classification)*

### Step 4: Execute Native Subagent (For current file)
Use the `Bash` tool to natively invoke the `cmp_summarizer` subagent via the Claude CLI. Pass the archived PDF path and the Hash ID, and pipe the output directly to the markdown file:
```bash
claude -p "$(< .claude/agents/cmp_summarizer.md)

The unique Hash ID for this paper is: <HashID>. Please read and summarize this paper: output_pdfs/<HashID>.pdf" > "data_md/<HashID>.md"
```
*(Note: Wait for this Bash command to finish completely before starting Step 1 for the next paper in the queue.)*

### Step 5: Batch Completion & Final Output
Once ALL papers in the queue have been successfully processed, verify the results.

**For Regular Papers:** Verify that the corresponding `.md` files exist in the `data_md/` directory.

**For Classified Files:** Verify that files were moved to the correct directories (`input_review/`, `input_book/`, `input_supp/`).

Present a comprehensive summary to the user detailing the batch results. For example:
"Successfully processed 5 files:

**Regular Papers (summarized):**
1. `Zhu2025.pdf` -> Archived as `<HashID_1>.pdf`, summary saved to `data_md/<HashID_1>.md`
2. `Wang2023.pdf` -> Archived as `<HashID_2>.pdf`, summary saved to `data_md/<HashID_2>.md`

**Classified Files (not summarized):**
3. `ReviewArticle2024.pdf` -> Classified as Review -> moved to `input_review/`
4. `BookChapter2022.pdf` -> Classified as Book -> moved to `input_book/`
5. `Supplementary_SI.pdf` -> Classified as Supplement -> moved to `input_supp/`"

**CRITICAL RULE: DO NOT print the actual markdown summaries in the main chat window. Only report the file paths, Hash IDs, and classification results.**