/**
 * math_renderer.js — Render công thức toán học LaTeX → Word/Image
 *
 * Su dung:
 *   node math_renderer.js <formula> [output.png]
 *   Hoac: require('./math_renderer').render(latex) → {svg, png, latex}
 *
 * Cac cach render:
 *   1. SVG inline (cho HTML/Markdown) - Giai phap tot nhat
 *   2. PNG image (cho DOCX) - Dung vi` docx khong ho tro MathML
 *   3. Unicode math (cho plain text) - Fallback
 *
 * Khoi can npm install — chi can Node.js co ban.
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// ═══════════════════════════════════════════════════════════════════════════
// CAU HINH
// ═══════════════════════════════════════════════════════════════════════════

const DPI = 150;           // Do phan giai PNG (150-300 cho in, 72-100 cho web)
const FONT_SIZE = 14;      // Font size cho PNG (pt)
const BG_COLOR = "FFFFFF"; // Mau nen (trang)

// LaTeX preamble toi thieu
const LATEX_PREAMBLE = `
\\documentclass[14pt]{article}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{amsfonts}
\\usepackage{geometry}
\\geometry{paperwidth=600pt,paperheight=100pt,margin=10pt}
\\begin{document}
\\thispagestyle{empty}
\\begin{align*}
`;

// ═══════════════════════════════════════════════════════════════════════════
// LUU TRU TEMPLATE
// ═══════════════════════════════════════════════════════════════════════════

// Map latex → unicode cho fallback khong co pdflatex
const UNICODE_MAP = {
  // Greek letters
  "\\alpha": "α", "\\beta": "β", "\\gamma": "γ", "\\delta": "δ",
  "\\epsilon": "ε", "\\zeta": "ζ", "\\eta": "η", "\\theta": "θ",
  "\\iota": "ι", "\\kappa": "κ", "\\lambda": "λ", "\\mu": "μ",
  "\\nu": "ν", "\\xi": "ξ", "\\pi": "π", "\\rho": "ρ",
  "\\sigma": "σ", "\\tau": "τ", "\\upsilon": "υ", "\\phi": "φ",
  "\\chi": "χ", "\\psi": "ψ", "\\omega": "ω",

  // Uppercase Greek
  "\\Alpha": "Α", "\\Beta": "Β", "\\Gamma": "Γ", "\\Delta": "Δ",
  "\\Theta": "Θ", "\\Lambda": "Λ", "\\Xi": "Ξ", "\\Pi": "Π",
  "\\Sigma": "Σ", "\\Phi": "Φ", "\\Psi": "Ψ", "\\Omega": "Ω",

  // Symbols
  "\\infty": "∞", "\\pm": "±", "\\mp": "∓", "\\times": "×",
  "\\div": "÷", "\\cdot": "·", "\\leq": "≤", "\\geq": "≥",
  "\\neq": "≠", "\\approx": "≈", "\\equiv": "≡",
  "\\sum": "∑", "\\prod": "∏", "\\int": "∫",
  "\\partial": "∂", "\\nabla": "∇", "\\forall": "∀",
  "\\exists": "∃", "\\in": "∈", "\\notin": "∉",
  "\\subset": "⊂", "\\supset": "⊃", "\\cup": "∪", "\\cap": "∩",

  // Superscripts
  "^{2}": "²", "^{3}": "³", "^{0}": "⁰", "^{1}": "¹",
  "^{+}": "⁺", "^{-}": "⁻", "^{n}": "ⁿ",

  // Subscripts
  "_{0}": "₀", "_{1}": "₁", "_{2}": "₂", "_{3}": "₃",
  "_{s}": "ₛ", "_{b}": "ᵦ", "_{c}": "꜀",

  // Fractions (toi da 2 chu so thap phan)
  "\\frac{a}{b}": "(a/b)",

  // Square root
  "\\sqrt{x}": "√x", "\\sqrt{x^2}": "√(x²)",
};

// ═══════════════════════════════════════════════════════════════════════════
// CAC HAM XU LY
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Chuyen LaTeX → Unicode (fallback khi khong co pdflatex)
 */
function latexToUnicode(latex) {
  let result = latex
    .replace(/\\\n/g, " ")           // Xu ly xuong dong
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1/$2)")  // Fraction
    .replace(/\\sqrt\{([^}]+)\}/g, "√($1)")              // Square root
    .replace(/\\overline\{([^}]+)\}/g, "($1̄)")           // Vinculum
    .replace(/\\hat\{([^}]+)\}/g, "($1̂)")                // Hat
    .replace(/\\vec\{([^}]+)\}/g, "($1⃗)")                // Vector
    .replace(/\{([^}]+)\}/g, "$1");                       // Remove braces

  // Apply unicode map
  for (const [latex, unicode] of Object.entries(UNICODE_MAP)) {
    result = result.split(latex).join(unicode);
  }

  return result;
}

/**
 * Lam sach ma nguon LaTeX
 */
function cleanLatex(latex) {
  return latex
    .replace(/^\s+|\s+$/g, "")           // Trim
    .replace(/\s+/g, " ")                 // Normalize spaces
    .replace(/\\text\{([^}]+)\}/g, "$1")  // \text{} → plain text
    .replace(/\\mathbf\{([^}]+)\}/g, "$1") // \mathbf{} → plain
    .replace(/\\mathrm\{([^}]+)\}/g, "$1") // \mathrm{} → plain
    .replace(/\\\(/g, "")                  // Remove \( \)
    .replace(/\\\)/g, "")                  //
    .replace(/\$\$?/g, "");               // Remove $$ or $
}

/**
 * Tao PNG tu LaTeX su dung pdflatex + convert (ImageMagick)
 * Tra ve Buffer hoac null neu khong thanh cong
 */
function renderToPng(latex, outputPath) {
  const tempDir = path.dirname(outputPath || __dirname);
  const baseName = `math_${Date.now()}`;
  const texFile = path.join(tempDir, `${baseName}.tex`);
  const pdfFile = path.join(tempDir, `${baseName}.pdf`);
  const pngFile = outputPath || path.join(tempDir, `${baseName}.png`);

  try {
    // Tao file LaTeX
    const fullLatex = `${LATEX_PREAMBLE}
${latex}
\\end{align*}
\\end{document}`;

    fs.writeFileSync(texFile, fullLatex, "utf8");

    // Compile pdflatex
    execSync(`pdflatex -interaction=batchmode -halt-on-error "${texFile}"`, {
      cwd: tempDir,
      stdio: "pipe"
    });

    // Convert PDF → PNG
    execSync(`magick -density ${DPI} "${pdfFile}" -transparent white "${pngFile}"`, {
      stdio: "pipe"
    });

    // Cleanup
    [texFile, pdfFile, pdfFile.replace(".pdf", ".aux"), pdfFile.replace(".pdf", ".log")]
      .forEach(f => { try { fs.unlinkSync(f); } catch(e) {} });

    return fs.readFileSync(pngFile);

  } catch (e) {
    console.warn(`⚠️ Khong the render LaTeX: ${e.message}`);
    return null;
  }
}

/**
 * Tao SVG tu LaTeX (cho HTML/Markdown)
 * Su dung latex-to-svg hoac fallback
 */
function renderToSvg(latex) {
  // Thu su dung latex-to-svg neu co
  try {
    // Cach 1: Su dung latex-to-svg (neu da cai dat)
    // const latexToSvg = require('latex-to-svg');
    // return latexToSvg(latex);
  } catch(e) {}

  // Cach 2: Fallback - tra ve Unicode voi SVG wrapper
  const unicode = latexToUnicode(latex);
  const encoded = encodeURIComponent(unicode);
  return `<svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 0 ${unicode.length * 10} 20">
    <text x="0" y="15" font-family="Times New Roman" font-size="14">${unicode}</text>
  </svg>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// API CHINH
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Render mot công thức toan hoc
 *
 * @param {string} latex - Ma nguon LaTeX
 * @param {Object} options - Cac tuy chon
 * @param {string} options.format - 'unicode' | 'png' | 'svg'
 * @param {string} options.output - Duong dan file output (cho PNG)
 * @returns {Object} - { text, image?, latex, formula }
 */
function render(latex, options = {}) {
  const format = options.format || "unicode";
  const cleanLtx = cleanLatex(latex);

  const result = {
    latex: cleanLtx,
    original: latex,
    format: format
  };

  switch (format) {
    case "unicode":
      result.text = latexToUnicode(cleanLtx);
      result.html = `<span class="math">${result.text}</span>`;
      break;

    case "svg":
      result.svg = renderToSvg(cleanLtx);
      result.text = latexToUnicode(cleanLtx);
      break;

    case "png":
      const pngBuffer = renderToPng(cleanLtx, options.output);
      if (pngBuffer) {
        result.image = pngBuffer;
        result.imagePath = options.output;
        result.text = latexToUnicode(cleanLtx);
      } else {
        // Fallback ve unicode
        result.text = latexToUnicode(cleanLtx);
        result.fallback = true;
      }
      break;

    default:
      result.text = latexToUnicode(cleanLtx);
  }

  return result;
}

/**
 * Render nhieu công thức tr mot chuoi
 *
 * @param {string} text - Chuoi co chua $...$ hoac $$...$$
 * @param {Object} options - Cac tuy chon
 * @returns {string} - Chuoi da duoc replace voi ky hieu phu hop
 */
function renderInline(text, options = {}) {
  const format = options.format || "unicode";

  // Tach cac block LaTeX
  const parts = text.split(/(\$\$?[^$]+\$\$?)/g);

  return parts.map(part => {
    // Block LaTeX ($...$ hoac $$...$$)
    if (part.match(/^\$[^*]/)) {
      const latex = part.replace(/^\$([^$]+)\$$/, "$1");
      const result = render(latex, { format, ...options });
      return result.text;
    }
    // Display LaTeX ($$...$$)
    else if (part.match(/^\$\$/)) {
      const latex = part.replace(/^\$\$([^$]+)\$\$$/, "$1");
      const result = render(latex, { format, ...options });
      return `\\displaystyle ${result.text}`;
    }
    // Plain text
    return part;
  }).join(" ");
}

// ═══════════════════════════════════════════════════════════════════════════
// VI DU SU DUNG
// ═══════════════════════════════════════════════════════════════════════════

function printExample() {
  console.log("\n═══════════════════════════════════════════════════");
  console.log("  MATH RENDERER - Vi du su dung");
  console.log("═══════════════════════════════════════════════════\n");

  const formulas = [
    "\\frac{M}{\\xi \\cdot R_b \\cdot b \\cdot h_0^2}",
    "\\alpha_f = \\frac{M}{R_b \\cdot b \\cdot h_0^2}",
    "A_s = \\frac{M}{0.9 \\cdot f_y \\cdot h_0}",
    "f = \\frac{5}{384} \\cdot \\frac{q \\cdot L^4}{E \\cdot I}",
  ];

  formulas.forEach((f, i) => {
    const result = render(f);
    console.log(`Cong thuc ${i + 1}:`);
    console.log(`  LaTeX: ${f}`);
    console.log(`  Unicode: ${result.text}`);
    console.log();
  });

  // Vi du inline
  const text = "Theo TCVN 5574:2018, he so $\\alpha_f = M/(R_b bh_0^2)$ duoc tinh nhu sau:";
  console.log("Vi du inline:");
  console.log(`  Goc: ${text}`);
  console.log(`  Rendered: ${renderInline(text)}`);
  console.log();
}

// ═══════════════════════════════════════════════════════════════════════════
// CLI
// ═══════════════════════════════════════════════════════════════════════════

if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === "--help") {
    console.log(`
╔═══════════════════════════════════════════════════════════════╗
║              MATH RENDERER - Huong dan su dung                ║
╠═══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Su dung don le:                                             ║
║    node math_renderer.js <formula> [output.png]              ║
║                                                              ║
║  Vi du:                                                      ║
║    node math_renderer.js "\\\\frac{M}{\\\\xi \\\\cdot R_b}"       ║
║    node math_renderer.js "A_s = \\\\frac{M}{0.9f_y h_0}" out.png  ║
║                                                              ║
║  Su dung trong Node.js:                                      ║
║    const {render, renderInline} = require('./math_renderer'); ║
║    const r = render('\\\\\\\\alpha = M/(R_b bh_0^2)');        ║
║    console.log(r.text); // In ra: α = M/(R_b bh_0²)          ║
║                                                              ║
║  Dac diem:                                                   ║
║    - Unicode: Cho Markdown/Text thong thuong                 ║
║    - PNG: Cho DOCX (can ImageMagick + pdflatex)             ║
║    - SVG: Cho HTML                                           ║
║                                                              ║
╚═══════════════════════════════════════════════════════════════╝
`);
    printExample();
    process.exit(0);
  }

  const latex = args[0];
  const outputPath = args[1];

  console.log(`\n  LaTeX: ${latex}`);

  // Unicode
  const unicode = render(latex);
  console.log(`  Unicode: ${unicode.text}`);

  // PNG neu co output path
  if (outputPath) {
    const png = render(latex, { format: "png", output: outputPath });
    if (png.image) {
      console.log(`  PNG: Da tao tai ${outputPath}`);
    } else {
      console.log(`  PNG: Khong tao duoc (can pdflatex + ImageMagick)`);
    }
  }

  console.log();
}

module.exports = { render, renderInline, latexToUnicode };
