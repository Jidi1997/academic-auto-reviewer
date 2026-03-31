import os
import re
import argparse

MD_DATABASE_DIR = "/path/to/your/markdown_database"

def clean_academic_noise(text):
    """
    学术噪音清洗器 V3：全面覆盖 SSRN 工作论文的特殊排版与符号。
    """
    # 1. 移除 DOI 和 SSRN 电子版链接
    text = re.sub(r'https?://doi\.org/[^\s]+', '', text)
    text = re.sub(r'doi:10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^.*Electronic copy available at:?.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^.*SSRN.*?abstract=\d+.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 2. 移除学术期刊的收稿/录用/编辑决定日期行
    text = re.sub(r'^Received .*?(?:Accepted|editorial decision).*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Available online .*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Advance Access publication.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 3. 移除版权声明、Permissions
    text = re.sub(r'^.*©.*(?:All rights reserved|Published by).*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^\d{4}-\d{4}/©.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^.*For permissions, please e-mail:.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 4. 移除特定的期刊页眉/页脚
    text = re.sub(r'^(?:The\s)?Review of Financial Studies.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^.*?\d+\s*\(\d{4}\)\s*\d+$', '', text, flags=re.MULTILINE)
    
    # 5. 移除 Markdown 图片占位符 和 单行作者页眉
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'^.*et al\.$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 6. 全面猎杀冗长致谢
    text = re.sub(r'^.*?(?:The authors thank|For helpful comments|We thank|I thank).*?(?:comments|Editor|referees?|participants).*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^.*Send correspondence to.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 7. 猎杀带有特殊符号的作者机构信息
    text = re.sub(r'^[\*†‡§‖¶]+\s*.*?(?:School|College|University|Department|Faculty|Institute|Business).*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 8. 压缩连续空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 9. 清除中文学术噪音
    text = re.sub(
        r'^\(C\)\s*\d{4}[-–]\d{4}\s*China Academic Journal.*?http://www\.cnki\.net\s*$',
        '', text, flags=re.MULTILINE | re.IGNORECASE
    )
    text = re.sub(
        r'^[^\n]*(?:大学|学院|研究院|政府|研究所)[^\n]*(?:电话|E-mail|通信作者|e-mail)[^\n]*$',
        '', text, flags=re.MULTILINE | re.IGNORECASE
    )
    text = re.sub(
        r'^[^\n]*(?:国家自然科学基金|国家社会科学基金|教育部|省自然科学)[^\n]*（[\d、，]+）[^\n]*$',
        '', text, flags=re.MULTILINE
    )
    text = re.sub(
        r'^[^\n]*(?:衷心感谢|诚挚感谢|感谢匿名审稿)[^\n]*(?:文责自负|建议)[^\n]*$',
        '', text, flags=re.MULTILINE
    )
    text = re.sub(
        r'^[★☆①②③*†‡§]+\s*[^\n]*(?:大学|学院|研究院|研究所|政府)[^\n]*$',
        '', text, flags=re.MULTILINE
    )

    return text.strip()


def find_intro_end(clean_body):
    """找引言结束位置：引言标题之后，第一个同级或更高级标题的起始处。"""
    intro_match = re.search(
        r'\n(#{1,3})\s*[^\n]*(?:引言|introduction)\b[^\n]*',
        clean_body, re.IGNORECASE
    )
    if not intro_match:
        return None

    level = len(intro_match.group(1))
    search_start = intro_match.end()

    pattern = r'\n#{1,' + str(level) + r'}\s+[^\n]+'
    next_match = re.search(pattern, clean_body[search_start:])
    if next_match:
        return search_start + next_match.start()
    return len(clean_body)


def extract_core_sections(content):
    content = "\n" + content

    # 切除结尾垃圾
    junk_keywords = r'(?:\bReferences\b|\bBibliography\b|参考文献|\bAppendix\b|附录|\bAcknowledgments?\b|\bCRediT\b|\bDeclaration\b|\bConflict of\b|\bData availability\b|\bFunding\b|致谢|数据可用性)'
    parts = re.split(
        r'\n(?:#+|[一二三四五六七八九十百]+[、.．])\s*[^\n]*?' + junk_keywords,
        content, maxsplit=1, flags=re.IGNORECASE
    )
    clean_body = parts[0]

    total_len = len(clean_body)
    TOTAL_CHAR_BUDGET = 12000
    MAX_CONCLUSION_LEN = 8000

    # 找最后一个结论标题
    matches = list(re.finditer(
        r'\n(?:#+\s*|[一二三四五六七八九十百]+[、.．]\s*)([^\n]*(?:conclusion|concluding|结论)[^\n]*(?:\n|$))',
        clean_body, flags=re.IGNORECASE
    ))
    conclusion_match = matches[-1] if matches else None

    if total_len <= TOTAL_CHAR_BUDGET:
        return clean_body.strip()

    if conclusion_match:
        conclusion_start_idx = conclusion_match.start()
        conclusion_text = clean_body[conclusion_start_idx:].strip()[:MAX_CONCLUSION_LEN]
        conclusion_len = len(conclusion_text)
        char_budget_for_head = TOTAL_CHAR_BUDGET - conclusion_len

        intro_end_idx = find_intro_end(clean_body)
        if intro_end_idx is not None:
            head_limit = min(char_budget_for_head, intro_end_idx)
        else:
            head_limit = char_budget_for_head

        if head_limit >= conclusion_start_idx:
            return clean_body[:TOTAL_CHAR_BUDGET].strip()

        head_text = clean_body[:head_limit].strip()
        return f"{head_text}\n\n\n[... METHODOLOGY & ROBUSTNESS OMITTED TO SAVE TOKEN ...]\n\n\n{conclusion_text}"
    else:
        return clean_body[:TOTAL_CHAR_BUDGET].strip()


def read_literature(citekey, search_keywords=None):
    file_path = os.path.join(MD_DATABASE_DIR, f"{citekey}.md")
    
    if not os.path.exists(file_path):
        return '{"error": "FILE_NOT_FOUND", "message": "The requested citekey does not exist in the local database. Classify as neutral/unverifiable."}'
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = clean_academic_noise(content)

    if search_keywords:
        keywords = [k.strip() for k in search_keywords.split(',')]
        extracted_contexts = []
        for kw in keywords:
            pattern = re.compile(r'(.{0,1000}' + re.escape(kw) + r'.{0,1000})', re.IGNORECASE | re.DOTALL)
            matches = pattern.findall(content)
            if matches:
                extracted_contexts.append(f"[Context for '{kw}']: ...{matches[0]}...")
        
        if extracted_contexts:
            return "\n\n".join(extracted_contexts)
        else:
            return '{"error": "KEYWORD_NOT_FOUND", "message": "Keywords not found in text. Re-evaluate claim or classify as neutral/unverifiable."}'

    return extract_core_sections(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("citekey")
    parser.add_argument("--keywords", default=None)
    args = parser.parse_args()
    print(read_literature(args.citekey, args.keywords))