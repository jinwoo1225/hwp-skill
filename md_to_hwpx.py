#!/usr/bin/env python3
"""
md_to_hwpx.py — Markdown → 한글 HWPX 변환기
크로스플랫폼 (mac/Linux/Windows/WSL) — Python 3.7+

사용법:
  python md_to_hwpx.py input.md output.hwpx
  python md_to_hwpx.py input.md output.hwpx --template my_template.hwpx

필요 패키지: 표준 라이브러리만 (zipfile, re, os, argparse, tempfile, shutil)
"""

import argparse
import os
import re
import shutil
import tempfile
import zipfile
import sys


def md_to_paragraphs(md_text):
    """마크다운을 (text, style) 리스트로 변환.

    지원:
      - # / ## / ### 헤더
      - - 리스트
      - > 인용
      - ``` 코드 블록
      - | 표 | (단순화: 각 행을 한 paragraph로, 셀은 '  |  '로 join)
      - 빈 줄 → paragraph 구분
      - 그 외 일반 단락
    """
    paragraphs = []
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # 헤더
        if line.startswith("### "):
            paragraphs.append((line[4:].strip(), "h3"))
            i += 1
            continue
        if line.startswith("## "):
            paragraphs.append((line[3:].strip(), "h2"))
            i += 1
            continue
        if line.startswith("# "):
            paragraphs.append((line[2:].strip(), "h1"))
            i += 1
            continue

        # 표
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            for tl in table_lines:
                cells = [c.strip() for c in tl.split("|") if c.strip()]
                if cells and all(re.match(r"^[-:]+$", c) for c in cells):
                    continue
                text = "  |  ".join(cells)
                paragraphs.append((text, "table"))
            continue

        # 코드 블록
        if line.startswith("```"):
            i += 1
            code_buffer = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_buffer.append(lines[i])
                i += 1
            i += 1  # 닫는 ```
            for cl in code_buffer:
                paragraphs.append((cl, "code"))
            continue

        # 인용
        if line.startswith(">"):
            text = line[1:].strip()
            paragraphs.append((text, "quote"))
            i += 1
            continue

        # 리스트
        if re.match(r"^[\-\*]\s+", line):
            text = re.sub(r"^[\-\*]\s+", "", line)
            paragraphs.append((text, "list"))
            i += 1
            continue

        # 번호 리스트
        if re.match(r"^\d+\.\s+", line):
            text = re.sub(r"^\d+\.\s+", "", line)
            paragraphs.append((text, "list-num"))
            i += 1
            continue

        # 일반 단락
        paragraphs.append((line.strip(), "p"))
        i += 1

    return paragraphs


def strip_inline_html(text):
    """인라인 HTML(<span>...</span> 등)을 제거하고 텍스트만 남김.

    한글에서 직접 렌더 안 되는 inline HTML은 단순 제거. bold(**...**)는 유지.
    """
    # span/div 등 단순 태그 제거 (내용은 유지)
    text = re.sub(r"</?span[^>]*>", "", text)
    text = re.sub(r"</?div[^>]*>", "", text)
    text = re.sub(r"</?a[^>]*>", "", text)
    # bold 마크다운은 그대로 둠 (한글에서 인식 가능하면 그대로, 못하면 사용자 보정)
    return text


def xml_escape(text):
    """XML 특수문자 이스케이프."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def make_paragraph_xml(text, style="p"):
    """(text, style) → HWPX paragraph XML."""
    text = strip_inline_html(text)
    text = xml_escape(text)

    char_pr = "0"
    if style == "h1":
        char_pr = "1"
    elif style == "h2":
        char_pr = "2"
    elif style == "h3":
        char_pr = "3"
    elif style == "code":
        char_pr = "10"
    elif style == "quote":
        char_pr = "11"
    elif style == "table":
        char_pr = "12"
    elif style in ("list", "list-num"):
        char_pr = "13"

    return (
        f'<hp:p><hp:run charPrIDRef="{char_pr}"><hp:t>{text}</hp:t></hp:run></hp:p>'
    )


def find_template(args_template):
    """사용자 지정 또는 기본 템플릿 결정."""
    candidates = []
    if args_template:
        candidates.append(args_template)
    # 기본 후보 (사용자 워크스페이스 흔한 경로)
    candidates.extend(
        [
            os.path.expanduser(
                "~/Downloads/아카이브/제안요청서_.hwpx"
            ),
            os.path.expanduser("~/Downloads/제안요청서_.hwpx"),
            os.path.expanduser("~/Downloads/입찰공고서_.hwpx"),
            os.path.expanduser("~/Documents/templates/hwp/blank.hwpx"),
        ]
    )
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Markdown → 한글 HWPX 변환기 (크로스플랫폼)"
    )
    parser.add_argument("input_md", help="입력 마크다운 파일 경로")
    parser.add_argument("output_hwpx", help="출력 HWPX 파일 경로")
    parser.add_argument(
        "--template",
        default=None,
        help="HWPX 템플릿 (기본 자동 탐색)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_md):
        print(f"Error: 입력 파일 없음: {args.input_md}", file=sys.stderr)
        sys.exit(1)

    # 1. 템플릿 결정
    template = find_template(args.template)
    if not template:
        print(
            "Error: HWPX 템플릿이 없습니다. --template path/to/template.hwpx 지정",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"템플릿: {template}")

    # 2. 임시 디렉토리에 추출
    work_dir = tempfile.mkdtemp(prefix="md_to_hwpx_")
    try:
        with zipfile.ZipFile(template, "r") as zf:
            zf.extractall(work_dir)
        print(f"추출: {work_dir}")

        # 3. md 읽기
        with open(args.input_md, "r", encoding="utf-8") as f:
            md_text = f.read()

        # 4. md → paragraphs
        paragraphs = md_to_paragraphs(md_text)
        print(f"단락: {len(paragraphs)}개")

        # 5. section0.xml 업데이트
        section0_path = os.path.join(work_dir, "Contents", "section0.xml")
        with open(section0_path, "r", encoding="utf-8") as f:
            content = f.read()

        ns_match = re.search(r"<hs:sec[^>]*>", content)
        if not ns_match:
            print("Error: section0.xml에서 <hs:sec> 태그를 찾을 수 없음", file=sys.stderr)
            sys.exit(1)
        ns_tag = ns_match.group(0)

        sec_pr_match = re.search(r"<hp:secPr[^>]*>.*?</hp:secPr>", content, re.DOTALL)
        sec_pr = sec_pr_match.group(0) if sec_pr_match else ""

        paragraphs_xml = "".join(
            make_paragraph_xml(t, s) for t, s in paragraphs
        )
        new_section0 = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
            + ns_tag
            + sec_pr
            + paragraphs_xml
            + "</hs:sec>"
        )

        with open(section0_path, "w", encoding="utf-8") as f:
            f.write(new_section0)

        # 6. Preview/PrvText.txt 갱신
        preview_path = os.path.join(work_dir, "Preview", "PrvText.txt")
        preview_text = "\n".join(t for t, s in paragraphs)
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(preview_text)

        # 7. ZIP → HWPX
        if os.path.exists(args.output_hwpx):
            os.remove(args.output_hwpx)
        with zipfile.ZipFile(args.output_hwpx, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(work_dir):
                for file in files:
                    fp = os.path.join(root, file)
                    arcname = os.path.relpath(fp, work_dir)
                    zf.write(fp, arcname)

        size = os.path.getsize(args.output_hwpx)
        print(f"OK: {args.output_hwpx} ({size:,} bytes)")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
