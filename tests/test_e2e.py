"""E2E 테스트 for hwp-skill (md_to_hwpx.py).

표준 라이브러리 unittest만 사용 — 추가 의존성 0.
실행: python -m unittest discover tests/ -v
"""

import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Add parent (repo root) to sys.path so we can import md_to_hwpx
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import md_to_hwpx  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "md_to_hwpx.py"
TEMPLATE = REPO_ROOT / "examples" / "example.hwpx"


def run_cli(input_md: str, output_hwpx: str, template: str = None, timeout: int = 60):
    """md_to_hwpx.py CLI 실행."""
    cmd = [sys.executable, str(SCRIPT), input_md, output_hwpx]
    if template:
        cmd.extend(["--template", template])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def write_temp_md(content: str) -> str:
    """임시 md 파일 작성 + 경로 반환."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


class TestColorExtraction(unittest.TestCase):
    """색상 추출 함수 단위 테스트."""

    def test_red_named(self):
        text, color = md_to_hwpx.extract_color("**RED:중요**")
        self.assertEqual(text, "중요")
        self.assertEqual(color, "FF0000")

    def test_blue_named(self):
        text, color = md_to_hwpx.extract_color("**BLUE:참고**")
        self.assertEqual(color, "0000FF")

    def test_green_named(self):
        text, color = md_to_hwpx.extract_color("**GREEN:성공**")
        self.assertEqual(color, "008000")

    def test_yellow_named(self):
        text, color = md_to_hwpx.extract_color("**YELLOW:주의**")
        self.assertEqual(color, "CCCC00")

    def test_all_13_colors(self):
        from md_to_hwpx import extract_color
        colors = [
            ("RED", "FF0000"), ("BLUE", "0000FF"), ("GREEN", "008000"),
            ("YELLOW", "CCCC00"), ("ORANGE", "FF8C00"), ("PURPLE", "800080"),
            ("CYAN", "008B8B"), ("MAGENTA", "FF00FF"), ("GRAY", "808080"),
            ("GREY", "808080"), ("BLACK", "000000"), ("WHITE", "FFFFFF"),
            ("PINK", "FF69B4"),
        ]
        for name, hex_code in colors:
            with self.subTest(color=name):
                _, color = extract_color(f"**{name}:test**")
                self.assertEqual(color, hex_code)

    def test_hex_direct(self):
        text, color = md_to_hwpx.extract_color("**#FF6600:강조**")
        self.assertEqual(text, "강조")
        self.assertEqual(color, "FF6600")

    def test_html_inline_named(self):
        text, color = md_to_hwpx.extract_color('<span style="color:red">경고</span>')
        self.assertEqual(text, "경고")
        self.assertEqual(color, "FF0000")

    def test_html_inline_hex_6(self):
        text, color = md_to_hwpx.extract_color(
            '<span style="color: #ff0000">중요</span>'
        )
        self.assertEqual(color, "FF0000")

    def test_html_inline_hex_3_expanded(self):
        text, color = md_to_hwpx.extract_color('<span style="color:#f00">X</span>')
        self.assertEqual(color, "FF0000")

    def test_no_color_passthrough(self):
        text, color = md_to_hwpx.extract_color("일반 텍스트")
        self.assertEqual(text, "일반 텍스트")
        self.assertIsNone(color)

    def test_bold_only_no_color(self):
        text, color = md_to_hwpx.extract_color("**볼드만**")
        self.assertIsNone(color)


class TestMarkdownParsing(unittest.TestCase):
    """md_to_paragraphs 함수 단위 테스트."""

    def test_h1(self):
        paras = md_to_hwpx.md_to_paragraphs("# 제목")
        self.assertEqual(paras, [("제목", "h1")])

    def test_h2(self):
        paras = md_to_hwpx.md_to_paragraphs("## 부제")
        self.assertEqual(paras, [("부제", "h2")])

    def test_h3(self):
        paras = md_to_hwpx.md_to_paragraphs("### 소제")
        self.assertEqual(paras, [("소제", "h3")])

    def test_unordered_list(self):
        paras = md_to_hwpx.md_to_paragraphs("- 항목1\n- 항목2")
        self.assertEqual(paras, [("항목1", "list"), ("항목2", "list")])

    def test_ordered_list(self):
        paras = md_to_hwpx.md_to_paragraphs("1. 첫째\n2. 둘째")
        self.assertEqual(paras, [("첫째", "list-num"), ("둘째", "list-num")])

    def test_quote(self):
        paras = md_to_hwpx.md_to_paragraphs("> 인용문")
        self.assertEqual(paras, [("인용문", "quote")])

    def test_code_block(self):
        md = "```\nprint('hi')\nx = 1\n```"
        paras = md_to_hwpx.md_to_paragraphs(md)
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0][1], "code")
        self.assertIn("print('hi')", paras[0][0])

    def test_table_simple(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        paras = md_to_hwpx.md_to_paragraphs(md)
        # 구분선 제외, 2개 행
        self.assertEqual(len(paras), 2)
        self.assertEqual(paras[0][1], "table")
        self.assertIn("A", paras[0][0])
        self.assertIn("B", paras[0][0])


class TestParagraphXMLGeneration(unittest.TestCase):
    """make_paragraph_xml 함수 단위 테스트."""

    def test_basic_paragraph(self):
        xml = md_to_hwpx.make_paragraph_xml("테스트", "p")
        self.assertIn("<hp:p>", xml)
        self.assertIn("테스트", xml)
        self.assertIn('charPrIDRef="0"', xml)

    def test_h1_uses_charpr1(self):
        xml = md_to_hwpx.make_paragraph_xml("제목", "h1")
        self.assertIn('charPrIDRef="1"', xml)

    def test_h2_uses_charpr2(self):
        xml = md_to_hwpx.make_paragraph_xml("부제", "h2")
        self.assertIn('charPrIDRef="2"', xml)

    def test_list_uses_charpr13(self):
        xml = md_to_hwpx.make_paragraph_xml("항목", "list")
        self.assertIn('charPrIDRef="13"', xml)

    def test_color_uses_inline_rpr(self):
        xml = md_to_hwpx.make_paragraph_xml("**RED:test**", "p")
        self.assertIn("<hp:rPr>", xml)
        self.assertIn("<hp:color", xml)
        self.assertIn("#FF0000", xml)
        # 색상이 있으면 charPrIDRef 없어야 함
        self.assertNotIn("charPrIDRef", xml)

    def test_xml_escaping(self):
        xml = md_to_hwpx.make_paragraph_xml("<script>", "p")
        self.assertIn("&lt;script&gt;", xml)
        self.assertNotIn("<script>", xml)

    def test_ampersand_escaped(self):
        xml = md_to_hwpx.make_paragraph_xml("AT&T", "p")
        self.assertIn("AT&amp;T", xml)


class TestEndToEndConversion(unittest.TestCase):
    """전체 변환 e2e 테스트 — CLI 호출."""

    @classmethod
    def setUpClass(cls):
        if not TEMPLATE.exists():
            raise unittest.SkipTest(f"Template fixture not found: {TEMPLATE}")

    def _convert(self, md_content: str, template_path: str = None):
        """md → HWPX 변환 후 (md_path, hwpx_path, result) 반환."""
        md_path = write_temp_md(md_content)
        hwpx_path = md_path.replace(".md", ".hwpx")
        result = run_cli(md_path, hwpx_path, template=template_path)
        return md_path, hwpx_path, result

    def _cleanup(self, *paths):
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    def test_basic_conversion_succeeds(self):
        md_path, hwpx_path, result = self._convert("# 제목\n\n본문\n")
        try:
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
            self.assertTrue(os.path.exists(hwpx_path))
            self.assertGreater(os.path.getsize(hwpx_path), 1000)
        finally:
            self._cleanup(md_path, hwpx_path)

    def test_zip_integrity(self):
        md_path, hwpx_path, _ = self._convert("# 무결성 테스트\n")
        try:
            with zipfile.ZipFile(hwpx_path) as zf:
                bad = zf.testzip()
                self.assertIsNone(bad, f"corrupt entry: {bad}")
        finally:
            self._cleanup(md_path, hwpx_path)

    def test_color_mapping_e2e(self):
        md = "**RED:빨강**\n**BLUE:파랑**\n**GREEN:초록**\n"
        md_path, hwpx_path, _ = self._convert(md)
        try:
            with zipfile.ZipFile(hwpx_path) as zf:
                content = zf.read("Contents/section0.xml").decode("utf-8")
                self.assertIn("#FF0000", content, "RED not embedded")
                self.assertIn("#0000FF", content, "BLUE not embedded")
                self.assertIn("#008000", content, "GREEN not embedded")
        finally:
            self._cleanup(md_path, hwpx_path)

    def test_preview_text_e2e(self):
        md = "# 미리보기\n\n이 텍스트는 미리보기에 박혀야 합니다."
        md_path, hwpx_path, _ = self._convert(md)
        try:
            with zipfile.ZipFile(hwpx_path) as zf:
                txt = zf.read("Preview/PrvText.txt").decode("utf-8")
                self.assertIn("미리보기", txt)
                self.assertIn("미리보기에 박혀야", txt)
        finally:
            self._cleanup(md_path, hwpx_path)


class TestKoreanText(unittest.TestCase):
    """한글 인코딩 / UTF-8 처리."""

    @classmethod
    def setUpClass(cls):
        if not TEMPLATE.exists():
            raise unittest.SkipTest(f"Template fixture not found: {TEMPLATE}")

    def test_korean_basic(self):
        md_path = write_temp_md(
            "# 한글 제목\n\n한글 본문 — '작은따옴표' \"쌍따옴표\" 정상 처리.\n"
        )
        hwpx_path = md_path.replace(".md", ".hwpx")
        try:
            result = run_cli(md_path, hwpx_path, template=str(TEMPLATE))
            self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
            with zipfile.ZipFile(hwpx_path) as zf:
                content = zf.read("Contents/section0.xml").decode("utf-8")
                self.assertIn("한글", content)
                self.assertIn("쌍따옴표", content)
        finally:
            for p in (md_path, hwpx_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_korean_with_emoji(self):
        md_path = write_temp_md("# 진행상황 📊\n\n- ✅ 완료\n- 🔄 진행중\n- ❌ 실패\n")
        hwpx_path = md_path.replace(".md", ".hwpx")
        try:
            result = run_cli(md_path, hwpx_path, template=str(TEMPLATE))
            self.assertEqual(result.returncode, 0)
            with zipfile.ZipFile(hwpx_path) as zf:
                content = zf.read("Contents/section0.xml").decode("utf-8")
                self.assertIn("📊", content)
                self.assertIn("✅", content)
        finally:
            for p in (md_path, hwpx_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass


class TestHWPXStructure(unittest.TestCase):
    """HWPX 파일 구조 (필수 파일, XML 유효성)."""

    @classmethod
    def setUpClass(cls):
        if not TEMPLATE.exists():
            raise unittest.SkipTest(f"Template fixture not found: {TEMPLATE}")

    def test_required_files_present(self):
        md_path = write_temp_md("# 구조\n")
        hwpx_path = md_path.replace(".md", ".hwpx")
        try:
            run_cli(md_path, hwpx_path, template=str(TEMPLATE), timeout=30)
            with zipfile.ZipFile(hwpx_path) as zf:
                names = set(zf.namelist())
                required = {
                    "mimetype",
                    "version.xml",
                    "Contents/section0.xml",
                    "Contents/header.xml",
                    "META-INF/container.xml",
                    "Preview/PrvText.txt",
                }
                missing = required - names
                self.assertFalse(missing, f"Missing files: {missing}")
        finally:
            for p in (md_path, hwpx_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def test_section0_xml_valid(self):
        md_path = write_temp_md("# XML\n\n## sub\n\nbody\n")
        hwpx_path = md_path.replace(".md", ".hwpx")
        try:
            run_cli(md_path, hwpx_path, template=str(TEMPLATE), timeout=30)
            with zipfile.ZipFile(hwpx_path) as zf:
                content = zf.read("Contents/section0.xml").decode("utf-8")
                # valid XML?
                root = ET.fromstring(content)
                self.assertIn("sec", root.tag)  # <hs:sec>
        finally:
            for p in (md_path, hwpx_path):
                try:
                    os.unlink(p)
                except OSError:
                    pass


class TestErrorHandling(unittest.TestCase):
    """에러 핸들링."""

    def test_missing_input_file(self):
        result = run_cli("/nonexistent/path/to.md", "/tmp/out.hwpx")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("입력 파일 없음", result.stderr)

    def test_missing_template(self):
        md_path = write_temp_md("# test\n")
        try:
            result = run_cli(
                md_path, "/tmp/out.hwpx",
                template="/nonexistent/template.hwpx",
            )
            self.assertNotEqual(result.returncode, 0)
        finally:
            try:
                os.unlink(md_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
