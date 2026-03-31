#!/usr/bin/env python3
"""
preprocess_manuscript.py — Prepare a Markdown academic manuscript for review.

Subcommands:
    clean   Strip token-wasting elements (refs, images, tables, captions, TOC, footnotes)
    split   Split cleaned manuscript into per-chapter files

Usage:
    python preprocess_manuscript.py clean  INPUT.md OUTPUT.md
    python preprocess_manuscript.py split  INPUT.md OUTPUT_DIR/
"""

import argparse
import os
import re
import sys


# ─── Stripping filters ───────────────────────────────────────────────────────

def strip_references_section(lines):
    """Remove everything from the References/参考文献 heading onwards."""
    ref_pattern = re.compile(
        r'^#{1,3}\s+(?:References|Bibliography|参考文献)(?:\s|\{|$)',
        re.IGNORECASE
    )
    for i, line in enumerate(lines):
        if ref_pattern.match(line):
            return lines[:i]
    return lines


def strip_images(lines):
    """Remove Markdown image lines: ![alt](path){attrs}.
    Uses a two-pass approach to avoid catastrophic backtracking with re.DOTALL on large files.
    """
    out = []
    skip_until_close = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\s*!\[.*\]\(.*\)(?:\{.*\})?\s*$', stripped):
            continue
        if re.match(r'^\s*!\[', stripped) and '](' not in stripped:
            skip_until_close = True
            continue
        if skip_until_close:
            if re.search(r'\]\(.*\)', stripped):
                skip_until_close = False
            continue
        out.append(line)
    return out


def strip_tables(lines):
    """Remove Markdown tables (|...|), grid tables (+---+), and Pandoc simple/multiline tables."""
    out = []
    in_pandoc_table = False
    # Matches multiple columns of dashes separated by spaces (req >= 3 columns to avoid math eqns)
    pandoc_border_pat = re.compile(r'^\s*(?:-+\s+){2,}-+\s*$')
    pandoc_solid_border = re.compile(r'^\s*-{5,}\s*$')

    for line in lines:
        stripped = line.strip()

        # 1. Standard markdown tables
        if stripped.startswith('|') and stripped.endswith('|') and len(stripped) > 1:
            continue
        if re.match(r'^\|[\s\-:]+\|', stripped):
            continue

        # 2. Grid tables
        if re.match(r'^\+[-=+]+\+$', stripped):
            continue

        is_multi_dash_border = bool(pandoc_border_pat.match(line))
        is_solid_border = bool(pandoc_solid_border.match(line))
        prev_empty = len(out) == 0 or out[-1].strip() == ''

        if not in_pandoc_table:
            if is_multi_dash_border:
                in_pandoc_table = True
                # Remove the preceding line if it was a header
                if not prev_empty and len(out) > 0:
                    out.pop()
                continue
            elif is_solid_border and prev_empty:
                in_pandoc_table = True
                continue
            elif is_solid_border and not prev_empty:
                # Likely an alternate H2 setext header, keep it
                out.append(line)
            else:
                out.append(line)
        else:
            if stripped == '':
                in_pandoc_table = False
                out.append(line)
            continue

    return out


def strip_captions(lines):
    """Remove figure/table caption lines."""
    caption_pattern = re.compile(
        r'^\s*(?:Figure|Fig\.|Table|图|表)\s*\d',
        re.IGNORECASE
    )
    anchor_caption = re.compile(r'^\s*\[\]\{#.*?\}.*?(?:图|表|Figure|Table)\s*\d')
    return [l for l in lines if not caption_pattern.match(l) and not anchor_caption.match(l)]


def strip_toc_links(lines):
    """Remove table-of-contents blocks (lines that are purely internal links)."""
    toc_link = re.compile(r'^\s*>?\s*\[.*?\]\(#.*?\)\s*$')
    return [l for l in lines if not toc_link.match(l)]


def strip_toc_section(lines):
    """Remove TOC pages and content until the next major heading."""
    out = []
    skip = False
    toc_pattern = re.compile(r'^#+\s*(?:目\s*录|目录|图表目录|Table of Contents|Contents)\s*$', re.IGNORECASE)
    heading_pattern = re.compile(r'^#\s+')
    for line in lines:
        if not skip and toc_pattern.match(line):
            skip = True
            continue
        if skip:
            if heading_pattern.match(line):
                skip = False
                out.append(line)
            continue
        out.append(line)
    return out


def strip_footnote_definitions(lines):
    """Remove footnote definition blocks: [^N]: ... and continuation lines."""
    out = []
    in_footnote = False
    footnote_pat = re.compile(r'^\s*\[\^\w+\]:\s')
    for line in lines:
        if footnote_pat.match(line):
            in_footnote = True
            continue
        if in_footnote:
            if line.strip() == '' or line.startswith('    ') or line.startswith('\t'):
                continue
            else:
                in_footnote = False
                out.append(line)
        else:
            out.append(line)
    return out


def strip_empty_blockquotes(lines):
    """Remove blocks of consecutive lines that are just '>' with optional whitespace."""
    text = '\n'.join(lines)
    text = re.sub(r'^(?:>\s*\n)+>\s*(?:\n|$)', '', text, flags=re.MULTILINE)
    return text.split('\n')


def strip_empty_blocks(lines):
    """Collapse 3+ consecutive blank lines into 2."""
    out = []
    blank_count = 0
    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                out.append(line)
        else:
            blank_count = 0
            out.append(line)
    return out


def preprocess(text):
    """Apply all stripping filters in sequence."""
    lines = text.split('\n')
    lines = strip_references_section(lines)
    lines = strip_images(lines)
    lines = strip_tables(lines)
    lines = strip_captions(lines)
    lines = strip_toc_links(lines)
    lines = strip_toc_section(lines)
    lines = strip_footnote_definitions(lines)
    lines = strip_empty_blockquotes(lines)
    lines = strip_empty_blocks(lines)
    return '\n'.join(lines)


# ─── Chapter splitter ────────────────────────────────────────────────────────

def split_chapters(input_file, output_dir):
    """Split a cleaned manuscript into per-chapter files by H1 (fallback H2)."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    os.makedirs(output_dir, exist_ok=True)

    h1_splits = re.split(r'(^# [^\n]+)', content, flags=re.MULTILINE)
    h2_splits = re.split(r'(^## [^\n]+)', content, flags=re.MULTILINE)

    if len(h1_splits) > 2:
        chapters = h1_splits
        split_level = "H1"
    elif len(h2_splits) > 2:
        chapters = h2_splits
        split_level = "H2"
    else:
        out_path = os.path.join(output_dir, 'ch00_full.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        lines = content.count('\n') + 1
        print(f"⚠️  No H1 or H2 headings found. Wrote entire file as single chapter ({lines} lines).")
        return

    chapter_index = 0
    stats = []

    if chapters[0].strip():
        out_path = os.path.join(output_dir, f'ch{chapter_index:02d}_preface.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(chapters[0].strip() + '\n')
        lines = chapters[0].count('\n') + 1
        stats.append(f"  ch{chapter_index:02d}_preface.md — {lines} lines")
        chapter_index += 1

    for i in range(1, len(chapters), 2):
        heading = chapters[i]
        body = chapters[i+1] if i+1 < len(chapters) else ""
        safe_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '', heading.strip().replace('#', '').strip())
        filename = f'ch{chapter_index:02d}_{safe_name}.md'
        full_text = heading + body
        out_path = os.path.join(output_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(full_text + '\n')
        lines = full_text.count('\n') + 1
        chars = len(full_text)
        stats.append(f"  {filename} — {lines} lines, {chars} chars")
        chapter_index += 1

    print(f"Split {input_file} into {chapter_index} chapters (by {split_level}) at {output_dir}")
    for s in stats:
        print(s)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Preprocess academic manuscript: clean or split into chapters."
    )
    sub = parser.add_subparsers(dest="command")

    # clean subcommand
    p_clean = sub.add_parser("clean", help="Strip refs, images, tables, captions, TOC, footnotes")
    p_clean.add_argument("input", help="Input Markdown file")
    p_clean.add_argument("output", nargs="?", help="Output file (default: stdout)")

    # split subcommand
    p_split = sub.add_parser("split", help="Split cleaned manuscript into per-chapter files")
    p_split.add_argument("input", help="Input cleaned Markdown file")
    p_split.add_argument("output_dir", help="Directory to save chapter files")

    args = parser.parse_args()

    if args.command == "clean":
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
        result = preprocess(content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            orig_lines = len(content.split('\n'))
            new_lines = len(result.split('\n'))
            print(f"Preprocessed: {orig_lines} → {new_lines} lines ({orig_lines - new_lines} removed)")
        else:
            print(result)

    elif args.command == "split":
        split_chapters(args.input, args.output_dir)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
