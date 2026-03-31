"""
batch_factcheck_prep.py — Batch-resolve all manuscript citations against
a .bib file and fetch source content from the local Markdown database.

Outputs a single JSON file that Agent 3 (fact-checker) reads as input.

Usage:
    python batch_factcheck_prep.py INPUT_CLEAN.md OUTPUT.json
"""

import os
import sys
import re
import argparse
import json
import logging

# Ensure tools directory is in path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from read_literature import read_literature

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ─── Configuration ────────────────────────────────────────────────────────────
BIB_PATH = "/path/to/your/library.bib"
MD_DATABASE_DIR = "/path/to/your/markdown_database"


# ─── BibTeX Parsing ──────────────────────────────────────────────────────────

def parse_bib_file(bib_path=None):
    """Parse a .bib file into a list of dicts.

    Returns list of dicts with keys: citekey, author, first_author_key, year, title.
    Handles both 'year' and 'date' fields (date takes priority).
    """
    bib_path = bib_path or BIB_PATH

    try:
        with open(bib_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logging.error(f"Bib file not found: {bib_path}")
        return []

    entries = []
    raw_entries = re.split(r'\n@', '\n' + content)[1:]

    for raw in raw_entries:
        if '{' not in raw:
            continue

        first_line = raw.split(',', 1)[0]
        citekey = first_line.split('{', 1)[-1].strip()

        author_match = re.search(r'author\s*=\s*{([^}]+)}', raw, re.IGNORECASE)
        if not author_match:
            continue
        author_str = author_match.group(1).replace('\n', ' ')
        author_clean = re.sub(r'\{([^{}]*)\}', r'\1', author_str)
        author_clean = re.sub(r'\s+', ' ', author_clean).strip()

        year_match = (
            re.search(r'\bdate\s*=\s*\{(\d{4})', raw, re.IGNORECASE) or
            re.search(r'\byear\s*=\s*\{(\d{4})', raw, re.IGNORECASE) or
            re.search(r'\byear\s*=\s*(\d{4})\b', raw, re.IGNORECASE)
        )
        if not year_match:
            continue
        year = year_match.group(1)

        title_match = re.search(r'\btitle\s*=\s*\{([^}]+)', raw, re.IGNORECASE)
        title = title_match.group(1).replace('\n', ' ') if title_match else ""
        title = re.sub(r'\{([^{}]*)\}', r'\1', title)
        title = re.sub(r'\s+', ' ', title).strip()

        first_author = author_str.split(' and ')[0]
        if ',' in first_author:
            first_author = first_author.split(',')[0].strip()
        else:
            first_author = first_author.split(' ')[-1].strip()

        entries.append({
            "citekey": citekey,
            "author": author_clean,
            "first_author_key": first_author.lower(),
            "year": year,
            "title": title,
        })

    return entries


def resolve_first(author, year, entries=None):
    """Find the first matching bib entry for author + year.

    Returns the matching entry dict with 'in_database' flag, or None.
    """
    if entries is None:
        entries = parse_bib_file()

    author_lower = author.strip().lower()
    is_chinese = bool(re.search(r'[\u4e00-\u9fff]', author))

    for entry in entries:
        year_str = re.search(r'(\d{4})', entry["year"])
        if not year_str or year_str.group(1) != str(year).strip():
            continue

        if is_chinese:
            if author.strip() not in entry["author"]:
                continue
        else:
            if author_lower not in entry["first_author_key"] and author_lower not in entry["author"].lower():
                continue

        citekey = entry["citekey"]
        md_path = os.path.join(MD_DATABASE_DIR, f"{citekey}.md")
        return {**entry, "in_database": os.path.exists(md_path)}

    return None


# ─── Citation Extraction ─────────────────────────────────────────────────────

def extract_citations(md_path):
    """Extract standard APA/Author-Date style citation markers from manuscript.

    Handles citations that are split across multiple lines, e.g.:
        (Hartzmark和Shue,
        2023)
    """
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logging.error(f"Failed to read {md_path}: {e}")
        return []

    citations = []
    lines = text.split('\n')

    # Build a cumulative offset table: char_offset → line_number
    line_offsets = []
    offset = 0
    for i, line in enumerate(lines):
        line_offsets.append(offset)
        offset += len(line) + 1

    def char_to_line(pos):
        lo, hi = 0, len(line_offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_offsets[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def find_heading(line_num):
        for i in range(line_num - 1, -1, -1):
            if lines[i].startswith('#'):
                return lines[i].strip('# ').strip()
        return "Unknown"

    ALPHA_ACCENT = r'a-zA-Z\u00C0-\u017F'
    YEAR_PATTERN = r'[12][0-9]{3}[a-z]?(?:\s*[,，和与]\s*[12][0-9]{3}[a-z]?)*'
    single_cite = re.compile(
        r'[\(（]([' + ALPHA_ACCENT + r'\s\-\u4e00-\u9fa5]+)[,，]\s*(' + YEAR_PATTERN + r')[\)）]'
    )
    multi_cite = re.compile(
        r'[\(（]([' + ALPHA_ACCENT + r'\s\-\u4e00-\u9fa5,，0-9;；\s等和]+)[\)）]'
    )
    inner_cite = re.compile(
        r'([' + ALPHA_ACCENT + r'\s\-\u4e00-\u9fa5]+)[,，]\s*(' + YEAR_PATTERN + r')'
    )
    narrative_cite = re.compile(
        r'([' + ALPHA_ACCENT + r']+(?:\s+[A-Z])?(?:和[' + ALPHA_ACCENT + r']+(?:\s+[A-Z])?|及其合作者| et al\.|等)?|[\u4e00-\u9fa5]{2,5}(?:等|和[\u4e00-\u9fa5]{2,5})?)\s*[\(（](' + YEAR_PATTERN + r')[\)）]'
    )

    def _clean_author(author_text):
        primary = author_text.split('和')[0].split('等')[0].split('et al')[0].strip()
        if ' ' in primary and not any('\u4e00' <= c <= '\u9fa5' for c in primary):
            primary = primary.split(' ')[-1]
        return primary

    def get_context(line_num):
        start = max(0, line_num - 2)
        end = min(len(lines), line_num + 3) # Increased from +1 to +3 to catch multi-line citations fully
        return "\\n".join(lines[start:end]).strip()

    # Multi-citation blocks (semicolon-separated)
    for match in multi_cite.finditer(text):
        inner = match.group(1)
        if ';' not in inner and '；' not in inner:
            continue
        line_num = char_to_line(match.start())
        heading = find_heading(line_num)
        context = get_context(line_num)
        for part in re.split(r'[;；]', inner):
            m = inner_cite.search(part)
            if m:
                author_text, year = m.group(1).strip(), m.group(2).strip()
                citations.append({
                    "citation_text": f"({author_text}, {year})",
                    "location": f"{heading} · Line ~{line_num}",
                    "claim_context": context,
                    "search_author": _clean_author(author_text),
                    "search_year": year[:4]
                })

    # Single (Author, Year) patterns
    for match in single_cite.finditer(text):
        author_text, year = match.group(1).strip(), match.group(2).strip()
        line_num = char_to_line(match.start())
        citations.append({
            "citation_text": match.group(0).replace('\n', ' '),
            "location": f"{find_heading(line_num)} · Line ~{line_num}",
            "claim_context": get_context(line_num),
            "search_author": _clean_author(author_text),
            "search_year": year[:4]
        })

    # Narrative Author (Year) patterns
    for match in narrative_cite.finditer(text):
        author_text, year = match.group(1).strip(), match.group(2).strip()
        line_num = char_to_line(match.start())
        citations.append({
            "citation_text": match.group(0).replace('\n', ' '),
            "location": f"{find_heading(line_num)} · Line ~{line_num}",
            "claim_context": get_context(line_num),
            "search_author": _clean_author(author_text),
            "search_year": year[:4]
        })

    # [@citekey] syntax
    for match in re.compile(r'\[@([a-zA-Z0-9_]+)\]').finditer(text):
        line_num = char_to_line(match.start())
        citations.append({
            "citation_text": match.group(0),
            "location": f"Line ~{line_num}",
            "claim_context": get_context(line_num),
            "explicit_citekey": match.group(1)
        })

    return citations


# ─── Content Fetching ────────────────────────────────────────────────────────

def extract_paper_content(citekey):
    """Fetch key content from the local markdown database using read_literature.py."""
    try:
        content_str = read_literature(citekey)
        
        if content_str.startswith('{"error": "FILE_NOT_FOUND"'):
            return {"in_database": False}
            
        return {
            "in_database": True,
            "content_snippet": content_str
        }
    except Exception as e:
        logging.error(f"Error reading {citekey} via read_literature: {e}")
        return {"in_database": False}


# ─── Pipeline ────────────────────────────────────────────────────────────────

def process_manuscript(input_md, output_json):
    """Main pipeline: extract → resolve → fetch → JSON."""
    logging.info(f"Parsing bib database: {BIB_PATH}")
    bib_entries = parse_bib_file()
    logging.info(f"Loaded {len(bib_entries)} references.")

    logging.info(f"Extracting citations from: {input_md}")
    citations = extract_citations(input_md)
    logging.info(f"Found {len(citations)} citation markers (including repeated occurrences).")
    
    unique_raw_markers = set(c["citation_text"] for c in citations)
    logging.info(f"Unique citation markers: {len(unique_raw_markers)}")

    results = []
    processed_texts = set()

    for cit in citations:
        text = cit["citation_text"]
        unique_key = f"{text}_{cit['location']}"
        if unique_key in processed_texts:
            continue
        processed_texts.add(unique_key)

        result_item = {
            "citation_text": text,
            "location": cit["location"],
            "claim_context": cit.get("claim_context", "")
        }
        matched_entry = None

        if "explicit_citekey" in cit:
            target = cit["explicit_citekey"]
            for entry in bib_entries:
                if entry["citekey"] == target:
                    matched_entry = entry
                    break
        else:
            matched_entry = resolve_first(cit["search_author"], cit["search_year"], bib_entries)

        if matched_entry:
            citekey = matched_entry["citekey"]
            result_item["citekey"] = citekey
            result_item["title"] = matched_entry["title"]
            result_item.update(extract_paper_content(citekey))
        else:
            result_item["citekey"] = "UNKNOWN"
            result_item["in_database"] = False

        results.append(result_item)

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    unique_citekeys = set()
    unique_unresolved_texts = set()
    for r in results:
        if r.get("citekey") and r["citekey"] != "UNKNOWN":
            unique_citekeys.add(r["citekey"])
        else:
            unique_unresolved_texts.add(r.get("citation_text", ""))
    total_unique_papers = len(unique_citekeys) + len(unique_unresolved_texts)

    logging.info(f"Saved resolved citations to {output_json} (Total contexts: {len(results)})")
    logging.info(f"Unique literature references mapped: {total_unique_papers}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process manuscript citations via bib lookup and db fetch.")
    parser.add_argument("input_md", help="Path to cleaned input markdown file")
    parser.add_argument("output_json", help="Path to save output JSON")
    args = parser.parse_args()
    process_manuscript(args.input_md, args.output_json)
