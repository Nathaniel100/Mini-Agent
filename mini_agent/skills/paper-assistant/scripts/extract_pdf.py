#!/usr/bin/env python3
"""
PDF Paper Parser
Extract structured information from academic papers in PDF format.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from PDF file."""
    try:
        import pypdf
    except ImportError:
        print("Error: pypdf is required. Install with: uv pip install pypdf", file=sys.stderr)
        sys.exit(1)
    
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_metadata(text: str) -> dict:
    """Extract basic metadata from paper text."""
    lines = text.split('\n')
    lines = [l.strip() for l in lines if l.strip()]
    
    metadata = {
        "title": "",
        "authors": [],
        "abstract": "",
        "keywords": [],
        "doi": ""
    }
    
    # Extract title (usually first non-empty line or lines before first double newline)
    if lines:
        metadata["title"] = lines[0]
    
    # Extract DOI
    doi_pattern = r'10\.\d{4,}/[^\s]+'
    for line in lines:
        doi_match = re.search(doi_pattern, line)
        if doi_match:
            metadata["doi"] = doi_match.group()
            break
    
    # Extract keywords
    keyword_patterns = [
        r'Keywords?[:\s]+([^\n]+)',
        r'Index Terms?[:\s]+([^\n]+)',
    ]
    for pattern in keyword_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keywords_str = match.group(1)
            keywords = [k.strip() for k in re.split(r'[;,]', keywords_str) if k.strip()]
            metadata["keywords"] = keywords
            break
    
    return metadata


def extract_abstract(text: str) -> str:
    """Extract paper abstract."""
    # Common abstract patterns
    patterns = [
        r'Abstract[:\s]*\n?([^\n]+\n?.*?)(?=\n\s*(?:Introduction|Keywords|Index Terms)|$)',
        r'ABSTRACT[:\s]*\n?([^\n]+\n?.*?)(?=\n\s*(?:INTRODUCTION|KEYWORDS)|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # Clean up the abstract
            abstract = re.sub(r'\s+', ' ', abstract)
            return abstract
    
    return ""


def extract_sections(text: str) -> dict:
    """Extract paper sections and their content."""
    # Common academic paper section headers
    section_headers = [
        'Introduction', 'Related Work', 'Background', 'Methodology', 
        'Methods', 'Proposed Method', 'Approach', 'Experimental Setup',
        'Experiments', 'Results', 'Discussion', 'Conclusion', 
        'Conclusions', 'References', 'Acknowledgments'
    ]
    
    sections = {}
    lines = text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        # Check if line is a section header
        is_header = False
        for header in section_headers:
            # Match various header formats: "1. Introduction", "I. Introduction", "Introduction"
            if re.match(rf'^(?:\d+\.|[IVX]+\.?)\s+{re.escape(header)}$', line.strip(), re.IGNORECASE):
                is_header = True
                break
            elif re.match(rf'^{re.escape(header)}$', line.strip(), re.IGNORECASE):
                is_header = True
                break
        
        if is_header and current_section:
            sections[current_section] = '\n'.join(current_content)
            current_content = []
        
        # Set current section (handle numbered sections like "1 Introduction")
        for header in section_headers:
            if re.match(rf'^(?:\d+\.|[IVX]+\.?)\s+{re.escape(header)}$', line.strip(), re.IGNORECASE):
                current_section = header
                break
            elif re.match(rf'^{re.escape(header)}$', line.strip(), re.IGNORECASE):
                current_section = header
                break
        
        if current_section:
            current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def analyze_structure(text: str) -> dict:
    """Analyze paper structure."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    analysis = {
        "total_pages_estimate": len(text) // 3000,  # Rough estimate
        "word_count_estimate": len(text.split()),
        "has_figures": "Figure" in text or "Fig." in text,
        "has_tables": "Table" in text,
        "has_equations": any(c.isdigit() and '=' in line for line in lines[:100]),
        "references_count": len(re.findall(r'\[\d+\]', text))
    }
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description='Extract structured information from academic papers')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')
    parser.add_argument('--metadata-only', '-m', action='store_true', 
                        help='Extract only metadata (title, authors, abstract, keywords)')
    
    args = parser.parse_args()
    
    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    # Extract text
    text = extract_text_from_pdf(args.pdf_path)
    
    if args.metadata_only:
        result = extract_metadata(text)
        result["abstract"] = extract_abstract(text)
    else:
        # Full extraction
        metadata = extract_metadata(text)
        abstract = extract_abstract(text)
        sections = extract_sections(text)
        structure = analyze_structure(text)
        
        result = {
            "metadata": metadata,
            "abstract": abstract,
            "sections": sections,
            "structure": structure
        }
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Output written to: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
