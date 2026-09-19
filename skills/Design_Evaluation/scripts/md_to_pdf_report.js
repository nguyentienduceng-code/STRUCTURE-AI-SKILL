/**
 * md_to_pdf_report.js — Chuyen Markdown -> PDF kho A4, KHONG can npm dependency.
 *
 * Co che: render Markdown -> HTML self-contained, roi dung Chromium co san tren may
 * (Microsoft Edge / Google Chrome) o che do headless de in ra PDF.
 *
 * Ly do khong dung 'markdown-pdf': package do phu thuoc PhantomJS da ngung phat trien,
 * khong co trong node_modules cua skill nay va cai dat thuong that bai tren Windows.
 *
 * Dung:
 *   node md_to_pdf_report.js <input.md> <output.pdf> [--keep-html]
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const { spawnSync } = require("child_process");

// ---------------------------------------------------------------- CLI
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error("Usage: node md_to_pdf_report.js <input.md> <output.pdf> [--keep-html]");
  process.exit(1);
}
const inputMd = path.resolve(args[0]);
const outputPdf = path.resolve(args[1]);
const keepHtml = args.includes("--keep-html");

if (!fs.existsSync(inputMd)) {
  console.error(`❌ Khong tim thay file dau vao: ${inputMd}`);
  process.exit(1);
}

// ------------------------------------------------- Tim trinh duyet Chromium
function findBrowser() {
  const candidates = [
    process.env.CHROME_PATH,
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ].filter(Boolean);
  return candidates.find((p) => fs.existsSync(p)) || null;
}

// ------------------------------------------------------- Markdown -> HTML
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function inline(s) {
  return s
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_m, alt, src) => {
      const u = /^[a-z]+:\/\//i.test(src) ? src : "file:///" + path.resolve(path.dirname(inputMd), src).replace(/\\/g, "/");
      return `<img src="${u}" alt="${escapeHtml(alt)}">`;
    })
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/`([^`]+)`/g, (_m, c) => `<code>${escapeHtml(c)}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
}

function mdToHtml(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;
  let inCode = false;
  let listType = null;

  const closeList = () => {
    if (listType) { out.push(`</${listType}>`); listType = null; }
  };

  while (i < lines.length) {
    const line = lines[i];

    // Code fence
    if (/^```/.test(line)) {
      closeList();
      if (!inCode) { out.push("<pre><code>"); inCode = true; }
      else { out.push("</code></pre>"); inCode = false; }
      i++; continue;
    }
    if (inCode) { out.push(escapeHtml(line)); i++; continue; }

    // Bang Markdown
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      closeList();
      const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      const head = cells(line);
      i += 2;
      const body = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { body.push(cells(lines[i])); i++; }
      out.push("<table><thead><tr>" + head.map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>");
      body.forEach((r) => out.push("<tr>" + r.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>"));
      out.push("</tbody></table>");
      continue;
    }

    // Heading
    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) { closeList(); out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); i++; continue; }

    // Duong ke ngang
    if (/^\s*([-*_])\1{2,}\s*$/.test(line)) { closeList(); out.push("<hr>"); i++; continue; }

    // Trich dan
    if (/^\s*>\s?/.test(line)) {
      closeList();
      out.push(`<blockquote>${inline(line.replace(/^\s*>\s?/, ""))}</blockquote>`);
      i++; continue;
    }

    // Danh sach
    const ul = line.match(/^\s*[-*+]\s+(.*)$/);
    const ol = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ul || ol) {
      const want = ul ? "ul" : "ol";
      if (listType !== want) { closeList(); out.push(`<${want}>`); listType = want; }
      out.push(`<li>${inline((ul || ol)[1])}</li>`);
      i++; continue;
    }

    // Dong trong
    if (!line.trim()) { closeList(); i++; continue; }

    closeList();
    out.push(`<p>${inline(line)}</p>`);
    i++;
  }
  closeList();
  if (inCode) out.push("</code></pre>");
  return out.join("\n");
}

const CSS = `
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Times New Roman", "Segoe UI", serif; font-size: 12pt; line-height: 1.5; color: #111; }
h1 { font-size: 18pt; border-bottom: 2px solid #1a4f8a; padding-bottom: 6px; color: #1a4f8a; }
h2 { font-size: 15pt; color: #1a4f8a; margin-top: 18px; }
h3 { font-size: 13pt; margin-top: 14px; }
h4, h5, h6 { font-size: 12pt; margin-top: 12px; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #444; padding: 5px 7px; vertical-align: top; }
th { background: #dce6f1; font-weight: bold; text-align: left; }
tr:nth-child(even) td { background: #f6f8fb; }
code { font-family: Consolas, monospace; background: #f0f0f0; padding: 1px 4px; font-size: 10pt; }
pre { background: #f6f6f6; border-left: 3px solid #1a4f8a; padding: 8px 10px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { border-left: 4px solid #c0c0c0; margin: 8px 0; padding: 2px 12px; color: #444; }
img { max-width: 100%; page-break-inside: avoid; }
hr { border: none; border-top: 1px solid #bbb; margin: 14px 0; }
h1, h2, h3 { page-break-after: avoid; }
`;

const html = `<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<title>${escapeHtml(path.basename(inputMd, ".md"))}</title>
<style>${CSS}</style></head>
<body>
${mdToHtml(fs.readFileSync(inputMd, "utf8"))}
</body></html>`;

// -------------------------------------------------------------- Xuat file
fs.mkdirSync(path.dirname(outputPdf), { recursive: true });

const htmlPath = keepHtml
  ? outputPdf.replace(/\.pdf$/i, ".html")
  : path.join(fs.mkdtempSync(path.join(os.tmpdir(), "md2pdf-")), "report.html");
fs.writeFileSync(htmlPath, html, "utf8");

const browser = findBrowser();
if (!browser) {
  console.error(
    "❌ Khong tim thay Microsoft Edge / Google Chrome de in PDF.\n" +
    `   Da xuat ban HTML kho A4 tai: ${htmlPath}\n` +
    "   Mo file nay bang trinh duyet va chon In > Luu duoi dang PDF.\n" +
    "   Hoac dat bien moi truong CHROME_PATH tro toi file .exe cua trinh duyet."
  );
  process.exit(2);
}

const res = spawnSync(browser, [
  "--headless=new",
  "--disable-gpu",
  "--no-sandbox",
  "--no-pdf-header-footer",
  `--print-to-pdf=${outputPdf}`,
  "file:///" + htmlPath.replace(/\\/g, "/"),
], { encoding: "utf8", timeout: 120000 });

if (!fs.existsSync(outputPdf)) {
  console.error("❌ Khong tao duoc PDF.");
  if (res.stderr) console.error(res.stderr.split("\n").slice(0, 8).join("\n"));
  console.error(`   Ban HTML kho A4 van con tai: ${htmlPath}`);
  process.exit(3);
}

const kb = (fs.statSync(outputPdf).size / 1024).toFixed(1);
console.log(`✅ Da xuat PDF: ${outputPdf} (${kb} KB)`);
if (keepHtml) console.log(`   Ban HTML kem theo: ${htmlPath}`);
