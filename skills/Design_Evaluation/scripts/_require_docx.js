/**
 * _require_docx.js — Bo tai thu vien 'docx' mot cach ben vung.
 *
 * BOI CANH: Bo skill nay nam tren Google Drive (thu muc dong bo ao).
 * `npm install` chay truc tiep tren Drive THUONG THAT BAI voi loi EBADF,
 * de lai cac file 0 byte trong node_modules/ -> require('docx') crash voi
 * "Invalid package config".
 *
 * Module nay:
 *   1. Thu require('docx') theo duong dan chuan.
 *   2. Thu cac vi tri du phong (bien moi truong, node_modules cua skill).
 *   3. Neu that bai -> in huong dan sua CU THE, khong crash voi stack trace kho hieu.
 *
 * KHONG hardcode duong dan rieng cua mot may cu the.
 */

const fs = require("fs");
const path = require("path");

function tryRequire(p) {
  try {
    const m = require(p);
    if (m && typeof m === "object" && m.Document && m.Packer) return m;
  } catch (_) { /* bo qua, thu vi tri tiep theo */ }
  return null;
}

function isHealthy(dir) {
  try {
    return fs.statSync(path.join(dir, "package.json")).size > 0;
  } catch (_) {
    return false;
  }
}

function loadDocx() {
  const skillRoot = path.resolve(__dirname, "..");            // Design_Evaluation/
  const local = path.join(skillRoot, "node_modules", "docx");

  const candidates = [
    process.env.DOCX_PATH || null,                            // ghi de thu cong
    isHealthy(local) ? local : null,                          // node_modules cua skill
    "docx",                                                   // do phan giai chuan cua Node
  ].filter(Boolean);

  for (const c of candidates) {
    const m = tryRequire(c);
    if (m) return m;
  }

  console.error(
    "\n❌ Khong tai duoc thu vien 'docx'.\n" +
    (fs.existsSync(local) && !isHealthy(local)
      ? "   Nguyen nhan: goi 'docx' trong node_modules bi hong (file 0 byte),\n" +
        "   thuong do npm install chay truc tiep tren Google Drive that bai.\n"
      : "   Nguyen nhan: chua cai goi 'docx'.\n") +
    "\n   CACH SUA (cai o o dia local roi copy sang Drive):\n" +
    "     mkdir %TEMP%\\docxstage && cd %TEMP%\\docxstage\n" +
    "     npm install docx@^9.7.1\n" +
    `     xcopy /E /I /Y %TEMP%\\docxstage\\node_modules\\docx "${local}"\n` +
    "\n   Hoac tro bien moi truong DOCX_PATH toi mot ban 'docx' dang hoat dong:\n" +
    "     set DOCX_PATH=C:\\duong\\dan\\toi\\node_modules\\docx\n"
  );
  process.exit(1);
}

module.exports = loadDocx();
