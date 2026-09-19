"""
DOCX_Generator.py — Generator Thuyết minh Tính toán ra DOCX

Tạo file DOCX với font chuẩn Arial, format chuẩn TCVN.

Font chuẩn:
- Normal: Arial 12pt
- Heading 1: Arial 12pt Bold
- Heading 2: Arial 11pt Bold
- Heading 3: Arial 10pt Bold
- Table: Arial 11pt

Usage:
    python docx_generator.py --input TMTT.md --output TMTT.docx
    python docx_generator.py --input TMTT.md --output TMTT.docx --cover "Công trình ABC"
"""

import argparse
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from docx import Document
from docx.shared import Pt, Inches, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# =============================================================================
# CONSTANTS
# =============================================================================

# Font settings
NORMAL_FONT = 'Arial'
NORMAL_SIZE = Pt(12)
HEADING1_SIZE = Pt(14)
HEADING2_SIZE = Pt(13)
HEADING3_SIZE = Pt(12)
TABLE_SIZE = Pt(11)

# Colors
BLACK = None  # Default black

# =============================================================================
# MARKDOWN PARSER
# =============================================================================

class MarkdownParser:
    """Parse markdown và convert sang DOCX elements"""

    def __init__(self):
        self.doc: Optional[Document] = None
        self.styles_applied = {}

    def add_run_formatted(self, para, text: str, bold: bool = False, italic: bool = False, size: Pt = NORMAL_SIZE):
        """Add formatted text run"""
        run = para.add_run(text)
        run.font.name = NORMAL_FONT
        run.font.size = size
        run.font.bold = bold
        run.font.italic = italic
        # Set Vietnamese font
        run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)
        return run

    def parse_heading1(self, text: str) -> None:
        """Parse Heading 1"""
        para = self.doc.add_heading(text, level=1)
        for run in para.runs:
            run.font.name = NORMAL_FONT
            run.font.size = HEADING1_SIZE
            run.font.bold = True
            run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_heading2(self, text: str) -> None:
        """Parse Heading 2"""
        para = self.doc.add_heading(text, level=2)
        for run in para.runs:
            run.font.name = NORMAL_FONT
            run.font.size = HEADING2_SIZE
            run.font.bold = True
            run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_heading3(self, text: str) -> None:
        """Parse Heading 3"""
        para = self.doc.add_heading(text, level=3)
        for run in para.runs:
            run.font.name = NORMAL_FONT
            run.font.size = HEADING3_SIZE
            run.font.bold = True
            run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_table(self, lines: List[str]) -> None:
        """Parse markdown table to DOCX table"""
        if not lines:
            return

        # Count columns from first line
        header = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
        num_cols = len(header)

        # Skip separator line if exists
        start = 1
        if len(lines) > 1 and re.match(r'\|[\s\-:]+\|', lines[1]):
            start = 2

        # Create table
        table = self.doc.add_table(rows=0, cols=num_cols)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Add header row
        header_row = table.add_row()
        for i, cell_text in enumerate(header):
            cell = header_row.cells[i]
            cell.text = cell_text
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.name = NORMAL_FONT
                    run.font.size = TABLE_SIZE
                    run.font.bold = True
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

        # Add data rows
        for line in lines[start:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if not cells or len(cells) != num_cols:
                continue

            row = table.add_row()
            for i, cell_text in enumerate(cells):
                cell = row.cells[i]
                cell.text = cell_text
                for para in cell.paragraphs:
                    # Left align first column, center others
                    if i == 0:
                        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    else:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.name = NORMAL_FONT
                        run.font.size = TABLE_SIZE
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_code_block(self, lines: List[str]) -> None:
        """Parse code block (formulas)"""
        for line in lines:
            para = self.doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(1)
            for run in para.runs:
                run.text = line
                run.font.name = 'Courier New'
                run.font.size = Pt(10)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_list(self, line: str) -> None:
        """Parse list item"""
        para = self.doc.add_paragraph(style='List Bullet')
        # Remove leading bullet/dash
        text = re.sub(r'^[\-\*]\s*', '', line)
        para.add_run(text).font.name = NORMAL_FONT
        for run in para.runs:
            run.font.size = NORMAL_SIZE
            run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

    def parse_horizontal_rule(self) -> None:
        """Parse horizontal rule"""
        self.doc.add_paragraph('─' * 50)

    def parse_paragraph(self, text: str) -> None:
        """Parse regular paragraph"""
        para = self.doc.add_paragraph()
        para.add_run(text).font.name = NORMAL_FONT
        for run in para.runs:
            run.font.size = NORMAL_SIZE
            run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)


class DOCXGenerator:
    """Generator class cho DOCX output"""

    def __init__(self):
        self.parser = MarkdownParser()
        self.doc = Document()

    def set_document_properties(self, title: str = "", author: str = ""):
        """Set document properties"""
        core_props = self.doc.core_properties
        if title:
            core_props.title = title
        if author:
            core_props.author = author

    def add_cover_page(self, project_name: str, title: str = "THUYẾT MINH TÍNH TOÁN KẾT CẤU"):
        """Add cover page"""
        # Title
        para = self.doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(title)
        run.font.name = NORMAL_FONT
        run.font.size = Pt(20)
        run.font.bold = True
        run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

        self.doc.add_paragraph()

        # Project name
        para = self.doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(project_name)
        run.font.name = NORMAL_FONT
        run.font.size = Pt(16)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), NORMAL_FONT)

        self.doc.add_page_break()

    def parse_markdown_file(self, md_path: str) -> bool:
        """Parse markdown file to DOCX"""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.parser.doc = self.doc
            self.parse_markdown_content(content)
            return True
        except Exception as e:
            print(f"ERROR: Cannot parse markdown: {e}")
            return False

    def parse_markdown_content(self, content: str) -> None:
        """Parse markdown content"""
        lines = content.split('\n')
        i = 0
        in_code_block = False
        code_block_lines = []
        table_lines = []

        while i < len(lines):
            line = lines[i]

            # Code block
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_lines = []
                else:
                    in_code_block = False
                    self.parser.parse_code_block(code_block_lines)
                i += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue

            # Table
            if line.strip().startswith('|'):
                table_lines.append(line)
                i += 1
                # Check if table ends
                if i >= len(lines) or not lines[i].strip().startswith('|'):
                    self.parser.parse_table(table_lines)
                    table_lines = []
                continue

            if table_lines:
                self.parser.parse_table(table_lines)
                table_lines = []

            # Headings
            if line.startswith('# '):
                self.parser.parse_heading1(line[2:].strip())
            elif line.startswith('## '):
                self.parser.parse_heading2(line[3:].strip())
            elif line.startswith('### '):
                self.parser.parse_heading3(line[4:].strip())
            # Horizontal rule
            elif re.match(r'^-{3,}$', line.strip()):
                self.parser.parse_horizontal_rule()
            # List
            elif re.match(r'^[\-\*]\s', line):
                self.parser.parse_list(line)
            # Empty line
            elif not line.strip():
                pass
            # Regular paragraph
            elif line.strip():
                self.parser.parse_paragraph(line.strip())

            i += 1

        # Handle remaining table
        if table_lines:
            self.parser.parse_table(table_lines)

    def save(self, output_path: str) -> bool:
        """Save DOCX file"""
        try:
            self.doc.save(output_path)
            print(f"SUCCESS: DOCX saved to {output_path}")
            return True
        except Exception as e:
            print(f"ERROR: Cannot save DOCX: {e}")
            return False


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate DOCX from Thuyết minh markdown"
    )
    parser.add_argument("--input", "-i", required=True,
                       help="Input markdown file")
    parser.add_argument("--output", "-o", required=True,
                       help="Output DOCX file")
    parser.add_argument("--title", "-t",
                       help="Document title")
    parser.add_argument("--cover", "-c",
                       help="Project name for cover page")
    parser.add_argument("--no-cover", action="store_true",
                       help="Skip cover page")

    args = parser.parse_args()

    generator = DOCXGenerator()

    # Set properties
    if args.title:
        generator.set_document_properties(title=args.title)

    # Add cover page
    if args.cover and not args.no_cover:
        generator.add_cover_page(args.cover)

    # Parse markdown
    if not generator.parse_markdown_file(args.input):
        sys.exit(1)

    # Save
    if generator.save(args.output):
        print(f"\nGenerated: {args.output}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
