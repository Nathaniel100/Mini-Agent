---
name: paper-assistant
description: 学术论文分析与理解助手。用于分析 PDF 论文或网页链接，提取元数据、理解内容、总结贡献、解释术语、生成笔记和思维导图。当用户需要理解论文、总结论文内容、提取关键信息时使用此技能。
---

# Paper Assistant

## Overview

This skill enables Claude to analyze and understand academic papers in PDF format or web links. It provides comprehensive paper analysis capabilities including metadata extraction, content understanding, structure analysis, note-taking, terminology explanation, and interactive Q&A.

## Quick Start

To analyze a paper, follow these steps:

1. **Identify the paper source** - Determine if it's a PDF file or a web link
2. **Extract paper content** - Use the appropriate script to extract information
3. **Analyze the content** - Use reference prompts for specific analysis tasks
4. **Generate output** - Create notes, summaries, or answer questions

## Supported Formats

### PDF Papers
Use `scripts/extract_pdf.py` to extract structured information from PDF files.

```bash
# Full extraction (metadata + abstract + sections + structure)
python scripts/extract_pdf.py paper.pdf

# Metadata only (title, authors, abstract, keywords)
python scripts/extract_pdf.py paper.pdf --metadata-only

# Save output to file
python scripts/extract_pdf.py paper.pdf -o result.json
```

### Web Links
Use `scripts/extract_web.py` to extract paper information from web pages.

```bash
# Extract from arXiv
python scripts/extract_web.py "https://arxiv.org/abs/2301.12345"

# Extract from other sources
python scripts/extract_web.py "https://ieeexplore.ieee.org/document/123456"
```

## Core Capabilities

### 1. Paper Parsing (论文解析)

Extract metadata including title, authors, abstract, keywords, DOI, and publication venue.

**How to use:**
1. Run the extraction script for the paper
2. Parse the JSON output for metadata fields
3. Present the information in a structured format

**Example:** Extract the title, authors, and keywords from a PDF paper.

### 2. Content Understanding (内容理解)

Summarize the paper's core contributions, methods, and conclusions. Explain technical approaches in plain language.

**How to use:**
1. Use prompts from `references/analysis_prompts.md` (Section 2: 内容理解)
2. Provide the paper's abstract and key sections as input
3. Generate concise summaries in Chinese

**Example:** "Summarize this paper's main contributions" or "Explain this method in simple terms."

### 3. Structure Analysis (结构分析)

Analyze the paper's chapter structure, logical flow, and methodological pipeline.

**How to use:**
1. Use prompts from `references/analysis_prompts.md` (Section 3: 结构分析)
2. Extract section headings and content
3. Present the logical structure in a clear format

**Example:** "Analyze the structure of this paper" or "Describe the methodology flow."

### 4. Note Taking (笔记整理)

Generate structured reading notes and mind maps for paper understanding.

**How to use:**
1. Use `assets/note_template.md` for structured notes
2. Use `assets/mindmap_template.md` for mind map outlines
3. Fill in the templates with analysis results

**Example:** "Create reading notes for this paper" or "Generate a mind map of this paper."

### 5. Terminology Explanation (术语解释)

Explain specialized terminology and technical concepts from the paper.

**How to use:**
1. Reference `references/terminology.md` for common terms
2. Identify technical terms in the paper
3. Provide definitions with examples and analogies

**Example:** "What does [technical term] mean in this context?"

### 6. Timeline Analysis (时间线)

Trace the paper's publication history, related work, and citation relationships.

**How to use:**
1. Identify key terms and authors from the paper
2. Search for related work and historical context
3. Present the timeline and relationships

**Example:** "What is the history of this research area?" or "What papers built on this work?"

### 7. Interactive Q&A (问答交互)

Answer specific questions about the paper's content in depth.

**How to use:**
1. Use prompts from `references/analysis_prompts.md` (Section 7: 问答交互)
2. Reference the extracted paper content
3. Provide detailed, accurate answers

**Example:** "How does the proposed method compare to existing approaches?" or "What are the limitations of this study?"

## Resources

### scripts/

Contains executable Python scripts for paper extraction:

| Script | Purpose |
|--------|---------|
| `extract_pdf.py` | Extract structured information from PDF papers |
| `extract_web.py` | Extract paper information from web pages (arXiv, IEEE, etc.) |

**Dependencies:**
- `pypdf` - For PDF parsing
- `requests` - For web requests
- `beautifulsoup4` - For HTML parsing

Install dependencies:
```bash
uv pip install pypdf requests beautifulsoup4
```

### references/

Contains reference materials for analysis:

| File | Purpose |
|------|---------|
| `analysis_prompts.md` | Prompt templates for different analysis tasks |
| `terminology.md` | Terminology explanations and common academic abbreviations |

Load these files when performing specific analysis tasks to get detailed guidance and templates.

### assets/

Contains output templates:

| File | Purpose |
|------|---------|
| `note_template.md` | Structured paper reading note template |
| `mindmap_template.md` | Mind map outline template for paper analysis |

Use these templates to generate well-organized notes and visual summaries.

## Usage Examples

### Example 1: Extract Keywords from a PDF

```
User: 提取这篇 PDF 论文的关键词

Action:
1. Run: python scripts/extract_pdf.py paper.pdf --metadata-only
2. Parse the keywords field from JSON output
3. Present the keywords in a formatted list
```

### Example 2: Summarize Main Contributions

```
User: 帮我总结这篇论文的主要贡献

Action:
1. Extract paper abstract and conclusion sections
2. Use analysis_prompts.md Section 2 prompt
3. Generate a structured summary of contributions
```

### Example 3: Explain Method in Plain Language

```
User: 用通俗易懂的语言解释这篇论文的方法

Action:
1. Extract the methodology section
2. Use analysis_prompts.md Section 2 "通俗语言解释" prompt
3. Provide explanation with analogies and simple terms
```

## Dependencies

Install required Python packages:

```bash
uv pip install pypdf requests beautifulsoup4
```

---

*This skill provides comprehensive paper analysis capabilities for academic research assistance.*
