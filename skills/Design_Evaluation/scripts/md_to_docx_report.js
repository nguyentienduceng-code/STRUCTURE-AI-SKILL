/**
 * md_to_docx_report.js — Chuyen file Markdown (.md) sang Word (.docx).
 *
 * Dung:
 *   node md_to_docx_report.js <input.md> <output.docx>
 *
 * Ho tro: heading H1-H4, doan van, in dam / nghieng / code inline, danh sach
 * co thu tu & khong thu tu, bang Markdown, anh (duong dan tuyet doi), trich dan,
 * duong ke ngang, khoi code.
 *
 * Dinh dang: A4, Times New Roman 13pt, le T3cm - D3cm - T3cm - P2cm
 * (theo chuan trinh bay van ban hanh chinh Viet Nam).
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ImageRun,
} = require("./_require_docx");

// ------------------------------------------------------------------ CLI
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node md_to_docx_report.js <input.md> <output.docx>");
  process.exit(1);
}
const inputMd = path.resolve(args[0]);
const outputDocx = path.resolve(args[1]);

if (!fs.existsSync(inputMd)) {
  console.error(`❌ Khong tim thay file dau vao: ${inputMd}`);
  process.exit(1);
}
if (!/\.md$/i.test(inputMd)) {
  console.error(`❌ File dau vao phai la .md — nhan duoc: ${path.basename(inputMd)}`);
  console.error("   Neu ban co JSON handoff, dung generate_to_trinh.js hoac generate_report.py.");
  process.exit(1);
}

const FONT = "Times New Roman";
const FONT_OBJ = {
  name: FONT,
  ascii: FONT,
  cs: FONT,
  eastAsia: FONT,
  hAnsi: FONT
};
const SIZE = 26; // half-points => 13pt

// -------------------------------------------------- Inline -> TextRun[]
function inlineRuns(text, base = {}) {
  const runs = [];
  // Tach theo **dam**, *nghieng*, `code`
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  const push = (t, opt) => {
    if (t) runs.push(new TextRun({ text: t, font: FONT_OBJ, size: SIZE, ...base, ...opt }));
  };
  while ((m = re.exec(text)) !== null) {
    push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) push(tok.slice(2, -2), { bold: true });
    else if (tok.startsWith("`")) push(tok.slice(1, -1), { font: "Consolas", size: 22 });
    else push(tok.slice(1, -1), { italics: true });
    last = m.index + tok.length;
  }
  push(text.slice(last));
  return runs.length ? runs : [new TextRun({ text: "", font: FONT_OBJ, size: SIZE, ...base })];
}

const HEADING = [
  HeadingLevel.HEADING_1, HeadingLevel.HEADING_2,
  HeadingLevel.HEADING_3, HeadingLevel.HEADING_4,
  HeadingLevel.HEADING_5, HeadingLevel.HEADING_6,
];

const CELL_BORDER = {
  top: { style: BorderStyle.SINGLE, size: 1, color: "444444" },
  bottom: { style: BorderStyle.SINGLE, size: 1, color: "444444" },
  left: { style: BorderStyle.SINGLE, size: 1, color: "444444" },
  right: { style: BorderStyle.SINGLE, size: 1, color: "444444" },
};

function cell(text, isHeader) {
  return new TableCell({
    borders: CELL_BORDER,
    shading: isHeader ? { fill: "DCE6F1" } : undefined,
    children: [new Paragraph({
      children: inlineRuns(text, isHeader ? { bold: true } : {}),
      spacing: { before: 40, after: 40 },
    })],
  });
}

// ---------------------------------------------------- Markdown -> docx
function parse(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0, inCode = false, codeBuf = [];
  let missingImages = 0;

  const flushCode = () => {
    if (!codeBuf.length) return;
    codeBuf.forEach((l) => out.push(new Paragraph({
      children: [new TextRun({ text: l, font: "Consolas", size: 20 })],
      shading: { fill: "F4F4F4" },
      spacing: { before: 0, after: 0 },
    })));
    codeBuf = [];
  };

  while (i < lines.length) {
    const line = lines[i];

    if (/^```/.test(line)) {
      if (inCode) { flushCode(); inCode = false; } else inCode = true;
      i++; continue;
    }
    if (inCode) { codeBuf.push(line); i++; continue; }

    // Anh dung rieng mot dong
    const img = line.match(/^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$/);
    if (img) {
      const src = decodeURI(img[2].replace(/^file:\/\/\//, ""));
      const abs = path.isAbsolute(src) ? src : path.resolve(path.dirname(inputMd), src);
      if (fs.existsSync(abs)) {
        try {
          out.push(new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new ImageRun({
              data: fs.readFileSync(abs),
              transformation: { width: 560, height: 380 },
            })],
          }));
          if (img[1]) out.push(new Paragraph({
            alignment: AlignmentType.CENTER,
            children: inlineRuns(img[1], { italics: true }),
            spacing: { after: 160 },
          }));
        } catch (_) { missingImages++; }
      } else {
        missingImages++;
        console.warn(`⚠️  Khong tim thay anh: ${abs} — bo qua.`);
      }
      i++; continue;
    }

    // Bang
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const head = cells(line);
      i += 2;
      const rows = [new TableRow({ children: head.map((c) => cell(c, true)), tableHeader: true })];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        const r = cells(lines[i]);
        while (r.length < head.length) r.push("");
        rows.push(new TableRow({ children: r.slice(0, head.length).map((c) => cell(c, false)) }));
        i++;
      }
      out.push(new Table({ rows, width: { size: 100, type: WidthType.PERCENTAGE } }));
      out.push(new Paragraph({ text: "", spacing: { after: 120 } }));
      continue;
    }

    // Heading
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      out.push(new Paragraph({
        heading: HEADING[h[1].length - 1],
        children: inlineRuns(h[2], { bold: true }),
        spacing: { before: 240, after: 120 },
      }));
      i++; continue;
    }

    // Duong ke ngang
    if (/^\s*([-*_])\1{2,}\s*$/.test(line)) {
      out.push(new Paragraph({
        text: "",
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } },
        spacing: { before: 120, after: 120 },
      }));
      i++; continue;
    }

    // Trich dan
    if (/^\s*>\s?/.test(line)) {
      out.push(new Paragraph({
        children: inlineRuns(line.replace(/^\s*>\s?/, ""), { italics: true, color: "444444" }),
        indent: { left: 400 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: "C0C0C0", space: 8 } },
        spacing: { before: 60, after: 60 },
      }));
      i++; continue;
    }

    // Danh sach
    const ul = line.match(/^\s*[-*+]\s+(.*)$/);
    const ol = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ul || ol) {
      out.push(new Paragraph({
        children: inlineRuns((ul || ol)[1]),
        bullet: ul ? { level: 0 } : undefined,
        numbering: ol ? { reference: "md-ol", level: 0 } : undefined,
        indent: ol ? { left: 720, hanging: 360 } : undefined,
        spacing: { before: 40, after: 40 },
      }));
      i++; continue;
    }

    if (!line.trim()) { i++; continue; }

    out.push(new Paragraph({
      children: inlineRuns(line),
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 60, after: 60, line: 300 },
    }));
    i++;
  }
  flushCode();
  return { children: out, missingImages };
}

// ------------------------------------------------------------ Xuat file
(async () => {
  const { children, missingImages } = parse(fs.readFileSync(inputMd, "utf8"));

  const doc = new Document({
    numbering: {
      config: [{
        reference: "md-ol",
        levels: [{ level: 0, format: "decimal", text: "%1.", alignment: AlignmentType.START }],
      }],
    },
    styles: { default: { document: { run: { font: FONT_OBJ, size: SIZE } } } },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },              // A4
          margin: { top: 1701, bottom: 1701, left: 1701, right: 1134 }, // 3/3/3/2 cm
        },
      },
      children,
    }],
  });

  fs.mkdirSync(path.dirname(outputDocx), { recursive: true });
  fs.writeFileSync(outputDocx, await Packer.toBuffer(doc));

  const kb = (fs.statSync(outputDocx).size / 1024).toFixed(1);
  console.log(`✅ Da xuat Word: ${outputDocx} (${kb} KB)`);
  if (missingImages) console.log(`⚠️  ${missingImages} anh khong tim thay — da bo qua.`);
})().catch((e) => {
  console.error("❌ Loi khi tao file Word:", e.message);
  process.exit(1);
});
