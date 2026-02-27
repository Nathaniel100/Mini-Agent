#!/usr/bin/env python3
"""
Web Paper Parser
Extract structured information from academic paper web pages (arXiv, IEEE, ACM, etc.)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def extract_from_arxiv(url: str) -> dict:
    """Extract paper info from arXiv.org."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: requests and beautifulsoup4 are required. Install with: uv pip install requests beautifulsoup4", file=sys.stderr)
        sys.exit(1)
    
    # Get arXiv ID from URL
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Handle different arXiv URL formats
    # https://arxiv.org/abs/2301.12345
    # https://arxiv.org/pdf/2301.12345
    # arxiv:2301.12345
    arxiv_id = path.split('/')[-1].replace('.pdf', '')
    
    # Fetch the abstract page
    abstract_url = f"https://arxiv.org/abs/{arxiv_id}"
    response = requests.get(abstract_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract title
    title_tag = soup.find('h1', class_='title')
    title = title_tag.get_text(strip=True).replace('Title:', '').strip() if title_tag else ""
    
    # Extract authors
    authors = []
    authors_tag = soup.find('div', class_='authors')
    if authors_tag:
        author_links = authors_tag.find_all('a')
        authors = [a.get_text(strip=True) for a in author_links]
    
    # Extract abstract
    abstract_tag = soup.find('blockquote', class_='abstract')
    abstract = abstract_tag.get_text(strip=True).replace('Abstract:', '').strip() if abstract_tag else ""
    
    # Extract metadata
    meta_info = {}
    for meta in soup.find_all('div', class_='meta'):
        label = meta.find('div', class_='label')
        value = meta.find('div', class_='value')
        if label and value:
            key = label.get_text(strip=True).rstrip(':')
            val = value.get_text(strip=True)
            meta_info[key] = val
    
    return {
        "source": "arXiv",
        "url": url,
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "metadata": meta_info,
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    }


def extract_from_generic(url: str) -> dict:
    """Extract paper info from generic web pages."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: requests and beautifulsoup4 are required.", file=sys.stderr)
        sys.exit(1)
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    result = {
        "source": "generic",
        "url": url,
        "title": "",
        "authors": [],
        "abstract": ""
    }
    
    # Try to extract title
    if soup.title:
        result["title"] = soup.title.string
    
    # Try common meta tags
    meta_tags = {
        "title": ['og:title', 'twitter:title', 'citation_title'],
        "author": ['author', 'citation_author', 'og:article:author'],
        "abstract": ['og:description', 'twitter:description', 'citation_abstract'],
        "doi": ['citation_doi']
    }
    
    for meta in soup.find_all('meta'):
        name = meta.get('name', '').lower()
        prop = meta.get('property', '').lower()
        content = meta.get('content', '')
        
        for key, patterns in meta_tags.items():
            if any(p in name or p in prop for p in patterns):
                if key == "author" and content:
                    result[key] = [a.strip() for a in content.split(',')]
                else:
                    result[key] = content
    
    # Try to find abstract in page content
    if not result["abstract"]:
        abstract_patterns = [
            r'Abstract[:\s]*\n?([^\n]+\n?.*?)(?=\n\s*(?:Introduction|Keywords)|$)',
        ]
        page_text = soup.get_text()
        for pattern in abstract_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if match:
                result["abstract"] = match.group(1).strip()
                break
    
    return result


def detect_source(url: str) -> str:
    """Detect the source type of the URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if 'arxiv.org' in domain:
        return 'arxiv'
    elif 'ieee.org' in domain:
        return 'ieee'
    elif 'acm.org' in domain:
        return 'acm'
    elif 'nature.com' in domain:
        return 'nature'
    elif 'science.org' in domain:
        return 'science'
    elif 'springer.com' in domain:
        return 'springer'
    else:
        return 'generic'


def main():
    parser = argparse.ArgumentParser(description='Extract structured information from academic paper web pages')
    parser.add_argument('url', help='URL of the paper page')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')
    
    args = parser.parse_args()
    
    # Detect source and extract
    source = detect_source(args.url)
    
    if source == 'arxiv':
        result = extract_from_arxiv(args.url)
    else:
        result = extract_from_generic(args.url)
    
    result["detected_source"] = source
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Output written to: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
