/**
 * generate_to_trinh.js
 * Tạo Tờ Trình Word (.docx) từ dữ liệu JSON — Luồng 2 (không cần template)
 * 
 * Sử dụng: node generate_to_trinh.js <data.json> <output.docx>
 * Ví dụ:   node generate_to_trinh.js data.json To_Trinh_PA_Ket_Cau.docx
 * 
 * [BUG-01] Margin theo Nghị định 30/2020/NĐ-CP (trái 3cm, phải 2cm)
 * [BUG-02] Layout: Tên Công ty bên trái, Quốc hiệu bên phải
 * [BUG-03] CONTENT_WIDTH tính từ margin không đối xứng
 * [MISS-03] Auto-install docx nếu chưa có
 * [OPT-02] Hỗ trợ chèn hình ảnh vào Tờ Trình
 */

const fs = require("fs");
const path = require("path");

// ═══════════════════════════════════════════════════════════
// Tải thư viện docx qua resolver dùng chung (_require_docx.js).
// Resolver xử lý trường hợp node_modules bị hỏng do npm install
// thất bại trên Google Drive, và in hướng dẫn sửa cụ thể.
// ═══════════════════════════════════════════════════════════
const docxObj = require("./_require_docx");

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, ImageRun,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
  TabStopType, TabStopPosition, VerticalAlign
} = docxObj;

// ═══════════════════════════════════════════════════════════
// [BUG-01] CẤU HÌNH MARGIN THEO NGHỊ ĐỊNH 30/2020/NĐ-CP
// ═══════════════════════════════════════════════════════════
const FONT_MAIN = "Times New Roman";
const FONT_SIZE_BODY = 26;        // 13pt (docx-js dùng half-point)
const FONT_SIZE_TITLE = 30;       // 15pt
const FONT_SIZE_HEADING = 28;     // 14pt
const FONT_SIZE_SMALL = 22;       // 11pt
const FONT_SIZE_ORG = 26;         // 13pt cho tên cơ quan

const PAGE_A4_WIDTH = 11906;      // A4 width in DXA
const PAGE_A4_HEIGHT = 16838;     // A4 height in DXA

// Nghị định 30/2020/NĐ-CP: Lề trái 3cm, lề phải 2cm, trên 2cm, dưới 2cm
const MARGIN_LEFT = 1701;         // 3cm = 1701 DXA
const MARGIN_RIGHT = 1134;        // 2cm = 1134 DXA
const MARGIN_TOP = 1134;          // 2cm
const MARGIN_BOTTOM = 1134;       // 2cm

// [BUG-03] CONTENT_WIDTH tính chính xác từ margin không đối xứng
const CONTENT_WIDTH = PAGE_A4_WIDTH - MARGIN_LEFT - MARGIN_RIGHT; // 9071 DXA

// Chia 2 cột cho header (Cty trái ~45%, Quốc hiệu phải ~55%)
const COL_LEFT_WIDTH = Math.floor(CONTENT_WIDTH * 0.42);
const COL_RIGHT_WIDTH = CONTENT_WIDTH - COL_LEFT_WIDTH;

// ═══════════════════════════════════════════════════════════
// ĐỌC DỮ LIỆU JSON
// ═══════════════════════════════════════════════════════════
if (process.argv.length < 4) {
  console.log("═══════════════════════════════════════════════════");
  console.log("  TỜ TRÌNH GENERATOR — Luồng 2 (docx-js)");
  console.log("═══════════════════════════════════════════════════");
  console.log();
  console.log("Cách dùng: node generate_to_trinh.js <data.json> <output.docx>");
  console.log("Ví dụ:     node generate_to_trinh.js data.json To_Trinh_Final.docx");
  console.log();
  console.log("Xem file mẫu: data_to_trinh_sample.json");
  process.exit(1);
}

const jsonPath = process.argv[2];
const outputPath = process.argv[3];

if (!fs.existsSync(jsonPath)) {
  console.error(`❌ [LỖI] Không tìm thấy file JSON: ${jsonPath}`);
  process.exit(1);
}

let data;
try {
  data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
} catch (e) {
  console.error(`❌ [LỖI] File JSON không hợp lệ: ${e.message}`);
  process.exit(1);
}

// ═══════════════════════════════════════════════════════════
// [MỚI] KIỂM TRA DỮ LIỆU BẮT BUỘC (SCHEMA VALIDATION)
// ═══════════════════════════════════════════════════════════
const requiredFields = ["Ten_Du_An", "Ve_Viec", "Nguoi_Nhan", "Kien_Nghi"];
const missingFields = requiredFields.filter(field => !data[field]);

if (missingFields.length > 0) {
  console.error(`\n❌ [LỖI NGHIÊM TRỌNG] File JSON thiếu các trường dữ liệu bắt buộc!`);
  console.error(`   Các trường bị thiếu: ${missingFields.join(", ")}`);
  console.error(`   Vui lòng yêu cầu AI bổ sung đầy đủ trước khi xuất Tờ Trình.\n`);
  process.exit(1);
}

console.log(`📋 Đang tạo Tờ Trình từ: ${jsonPath}`);

// Lấy thư mục chứa file JSON để tính đường dẫn ảnh tương đối
const jsonDir = path.dirname(path.resolve(jsonPath));

// ═══════════════════════════════════════════════════════════
// HÀM TẠO CÁC THÀNH PHẦN
// ═══════════════════════════════════════════════════════════

const NO_BORDER = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const NO_BORDERS = { top: NO_BORDER, bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER };
const THIN_BORDER = { style: BorderStyle.SINGLE, size: 1, color: "000000" };
const TABLE_BORDERS = { top: THIN_BORDER, bottom: THIN_BORDER, left: THIN_BORDER, right: THIN_BORDER };
const CELL_MARGINS = { top: 40, bottom: 40, left: 80, right: 80 };

/** Tạo dòng text thường */
function bodyText(text, options = {}) {
  return new Paragraph({
    alignment: options.alignment || AlignmentType.JUSTIFIED,
    spacing: { after: options.after || 120, line: options.line || 312 },
    indent: options.indent ? { firstLine: 720 } : undefined,
    children: [
      new TextRun({
        text: text,
        font: FONT_MAIN,
        size: options.size || FONT_SIZE_BODY,
        bold: options.bold || false,
        italics: options.italics || false,
      }),
    ],
  });
}

/** Tạo heading mục (I. II. III...) */
function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    children: [
      new TextRun({
        text: text,
        font: FONT_MAIN,
        size: FONT_SIZE_HEADING,
        bold: true,
      }),
    ],
  });
}

/** Tạo bullet item */
function bulletItem(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level: level },
    spacing: { after: 60 },
    children: [
      new TextRun({
        text: text,
        font: FONT_MAIN,
        size: FONT_SIZE_BODY,
      }),
    ],
  });
}

/** [OPT-02] Chèn hình ảnh nếu file tồn tại */
function insertImage(imagePath, captionText, widthPx = 400) {
  const children = [];
  
  // Tính đường dẫn tuyệt đối dựa trên thư mục chứa file JSON
  const absoluteImagePath = path.resolve(jsonDir, imagePath);

  if (fs.existsSync(absoluteImagePath)) {
    const imageBuffer = fs.readFileSync(absoluteImagePath);
    const ext = path.extname(absoluteImagePath).replace(".", "").toLowerCase();
    const type = (ext === "jpg") ? "jpeg" : ext;
    
    // Tính tỷ lệ (giả định ảnh vuông nếu không biết kích thước thực)
    const heightPx = Math.floor(widthPx * 0.75);
    
    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 60 },
        children: [
          new ImageRun({
            type: type,
            data: imageBuffer,
            transformation: { width: widthPx, height: heightPx },
            altText: { title: captionText, description: captionText, name: path.basename(absoluteImagePath) },
          }),
        ],
      })
    );
    if (captionText) {
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [
            new TextRun({
              text: captionText,
              font: FONT_MAIN,
              size: FONT_SIZE_SMALL,
              italics: true,
            }),
          ],
        })
      );
    }
  } else {
    console.warn(`⚠️ Không tìm thấy ảnh: ${absoluteImagePath} — bỏ qua.`);
  }
  return children;
}

/** Tạo bảng so sánh phương án */
function createComparisonTable(phuongAnData) {
  if (!phuongAnData || phuongAnData.length === 0) return null;

  const headerShading = { fill: "D5E8F0", type: ShadingType.CLEAR };

  const headers = Object.keys(phuongAnData[0]);
  const colCount = headers.length;
  const colWidth = Math.floor(CONTENT_WIDTH / colCount);
  const columnWidths = Array(colCount).fill(colWidth);

  const headerRow = new TableRow({
    children: headers.map(h =>
      new TableCell({
        borders: TABLE_BORDERS,
        shading: headerShading,
        width: { size: colWidth, type: WidthType.DXA },
        margins: CELL_MARGINS,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: h, font: FONT_MAIN, size: FONT_SIZE_BODY, bold: true })],
        })],
      })
    ),
  });

  const dataRows = phuongAnData.map(row =>
    new TableRow({
      children: headers.map(h =>
        new TableCell({
          borders: TABLE_BORDERS,
          width: { size: colWidth, type: WidthType.DXA },
          margins: CELL_MARGINS,
          children: [new Paragraph({
            children: [new TextRun({ text: String(row[h] || ""), font: FONT_MAIN, size: FONT_SIZE_BODY })],
          })],
        })
      ),
    })
  );

  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: columnWidths,
    rows: [headerRow, ...dataRows],
  });
}

/** Tạo bảng Log Tính Toán */
function createCalculationLogsTable(logsData) {
  if (!logsData || logsData.length === 0) return null;

  const headerShading = { fill: "E0E0E0", type: ShadingType.CLEAR };
  const headers = ["Step", "Formula", "Values", "Result"];
  const colWidths = [
    Math.floor(CONTENT_WIDTH * 0.2),
    Math.floor(CONTENT_WIDTH * 0.3),
    Math.floor(CONTENT_WIDTH * 0.3),
    Math.floor(CONTENT_WIDTH * 0.2)
  ];

  const headerRow = new TableRow({
    children: headers.map((h, i) =>
      new TableCell({
        borders: TABLE_BORDERS,
        shading: headerShading,
        width: { size: colWidths[i], type: WidthType.DXA },
        margins: CELL_MARGINS,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: h, font: FONT_MAIN, size: FONT_SIZE_BODY, bold: true })],
        })],
      })
    ),
  });

  const dataRows = logsData.map(row =>
    new TableRow({
      children: headers.map((h, i) =>
        new TableCell({
          borders: TABLE_BORDERS,
          width: { size: colWidths[i], type: WidthType.DXA },
          margins: CELL_MARGINS,
          children: [new Paragraph({
            children: [new TextRun({ text: String(row[h] || ""), font: FONT_MAIN, size: FONT_SIZE_BODY })],
          })],
        })
      ),
    })
  );

  return new Table({
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

// ═══════════════════════════════════════════════════════════
// [BUG-02] HEADER: TÊN CÔNG TY (TRÁI) + QUỐC HIỆU (PHẢI)
// Theo Nghị định 30/2020/NĐ-CP — Mẫu văn bản hành chính
// ═══════════════════════════════════════════════════════════

const children = [];

// Dùng bảng ẩn viền để tạo layout 2 cột
const headerTable = new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: [COL_LEFT_WIDTH, COL_RIGHT_WIDTH],
  rows: [
    // Dòng 1: Tên công ty (trái) | Quốc hiệu (phải)
    new TableRow({
      children: [
        new TableCell({
          borders: NO_BORDERS,
          width: { size: COL_LEFT_WIDTH, type: WidthType.DXA },
          verticalAlign: VerticalAlign.TOP,
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: data.Ten_Cong_Ty || data.Don_Vi || "CÔNG TY CP CT SÓNG THẦN",
                font: FONT_MAIN, size: FONT_SIZE_ORG, bold: true,
              })],
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: data.Don_Vi_Phat_Hanh || "BAN QUẢN LÝ THIẾT KẾ",
                font: FONT_MAIN, size: FONT_SIZE_ORG, bold: true,
              })],
            }),
          ],
        }),
        new TableCell({
          borders: NO_BORDERS,
          width: { size: COL_RIGHT_WIDTH, type: WidthType.DXA },
          verticalAlign: VerticalAlign.TOP,
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
                font: FONT_MAIN, size: FONT_SIZE_ORG, bold: true,
              })],
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: "Độc lập — Tự do — Hạnh phúc",
                font: FONT_MAIN, size: FONT_SIZE_HEADING, bold: true,
              })],
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: "─────────────────",
                font: FONT_MAIN, size: FONT_SIZE_BODY,
              })],
            }),
          ],
        }),
      ],
    }),
    // Dòng 2: Số văn bản (trái) | Địa điểm, ngày (phải)
    new TableRow({
      children: [
        new TableCell({
          borders: NO_BORDERS,
          width: { size: COL_LEFT_WIDTH, type: WidthType.DXA },
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: `Số: ${data.So_Van_Ban || "......./TTr-QLTK"}`,
                font: FONT_MAIN, size: FONT_SIZE_BODY,
              })],
            }),
          ],
        }),
        new TableCell({
          borders: NO_BORDERS,
          width: { size: COL_RIGHT_WIDTH, type: WidthType.DXA },
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({
                text: `${data.Dia_Diem || "TP.HCM"}, ngày ${data.Ngay_Lap || new Date().toLocaleDateString("vi-VN")}`,
                font: FONT_MAIN, size: FONT_SIZE_BODY, italics: true,
              })],
            }),
          ],
        }),
      ],
    }),
  ],
});

children.push(headerTable);

// Khoảng trống sau header
children.push(new Paragraph({ spacing: { after: 200 } }));

// --- TIÊU ĐỀ TỜ TRÌNH ---
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text: "TỜ TRÌNH", font: FONT_MAIN, size: FONT_SIZE_TITLE, bold: true })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [new TextRun({
      text: `Về việc: ${data.Ve_Viec || data.Mo_Ta_Ngan || "[Mô tả ngắn gọn nội dung trình duyệt]"}`,
      font: FONT_MAIN, size: FONT_SIZE_BODY, italics: true,
    })],
  })
);

// --- KÍNH GỬI ---
children.push(
  bodyText(`Kính gửi: ${data.Nguoi_Nhan || "[Chức danh người nhận]"}`, { bold: true, indent: true })
);

// --- I. CĂN CỨ PHÁP LÝ ---
children.push(sectionHeading("I. CĂN CỨ PHÁP LÝ"));

const canCu = data.Can_Cu_Phap_Ly || [
  "Tiêu chuẩn thiết kế kết cấu áp dụng (TCVN/QCVN).",
  "Hồ sơ thiết kế kiến trúc được duyệt.",
  "Hợp đồng tư vấn thiết kế số [....].",
];
if (Array.isArray(canCu)) {
  canCu.forEach(c => children.push(bulletItem(c)));
} else {
  children.push(bodyText(String(canCu), { indent: true }));
}

// --- II. NỘI DUNG TRÌNH DUYỆT ---
children.push(sectionHeading("II. NỘI DUNG TRÌNH DUYỆT"));

if (data.Hien_Trang) {
  children.push(bodyText("1. Hiện trạng / Vấn đề:", { bold: true }));
  children.push(bodyText(data.Hien_Trang, { indent: true }));
}

if (data.Phan_Tich_So_Luoc) {
  children.push(bodyText("2. Phân tích sơ lược:", { bold: true }));
  children.push(bodyText(data.Phan_Tich_So_Luoc, { indent: true }));
}

// [OPT-02] Chèn hình ảnh minh họa nếu có
if (data.Hinh_Anh && Array.isArray(data.Hinh_Anh)) {
  data.Hinh_Anh.forEach(img => {
    const imgElements = insertImage(img.path || img.duong_dan, img.caption || img.mo_ta, img.width || 400);
    imgElements.forEach(el => children.push(el));
  });
}

if (data.Bang_So_Sanh) {
  children.push(bodyText("3. Bảng so sánh phương án:", { bold: true }));
  const table = createComparisonTable(data.Bang_So_Sanh);
  if (table) children.push(table);
}

if (data.Noi_Dung_Bo_Sung) {
  children.push(bodyText(data.Noi_Dung_Bo_Sung, { indent: true }));
}

if (data.Ma_Bao_Cao_Dinh_Kem) {
  children.push(
    bodyText(`(Chi tiết xem Báo cáo phân tích kỹ thuật đính kèm số ${data.Ma_Bao_Cao_Dinh_Kem})`, { italics: true, indent: true })
  );
}

// --- III. KIẾN NGHỊ ---
children.push(sectionHeading("III. KIẾN NGHỊ"));

if (data.Kien_Nghi) {
  if (Array.isArray(data.Kien_Nghi)) {
    data.Kien_Nghi.forEach(k => children.push(bulletItem(k)));
  } else {
    children.push(bodyText(data.Kien_Nghi, { indent: true }));
  }
}

if (data.Tac_Dong_Chi_Phi) {
  children.push(bodyText(`Tác động chi phí: ${data.Tac_Dong_Chi_Phi}`, { indent: true, italics: true }));
}
if (data.Tac_Dong_Tien_Do) {
  children.push(bodyText(`Tác động tiến độ: ${data.Tac_Dong_Tien_Do}`, { indent: true, italics: true }));
}

// --- IV. ĐỀ NGHỊ PHÊ DUYỆT ---
children.push(sectionHeading("IV. ĐỀ NGHỊ PHÊ DUYỆT"));
children.push(
  bodyText(
    data.De_Nghi_Phe_Duyet ||
    `Kính đề nghị ${data.Nguoi_Nhan || "[Chức danh]"} xem xét và phê duyệt nội dung tờ trình nêu trên để Phòng QLTK có cơ sở triển khai các bước tiếp theo.`,
    { indent: true }
  )
);

// --- PHẦN KÝ TÊN (2 cột dùng bảng ẩn viền) ---
children.push(new Paragraph({ spacing: { before: 600 } }));

const signatureTable = new Table({
  width: { size: CONTENT_WIDTH, type: WidthType.DXA },
  columnWidths: [Math.floor(CONTENT_WIDTH * 0.45), Math.floor(CONTENT_WIDTH * 0.55)],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders: NO_BORDERS,
          width: { size: Math.floor(CONTENT_WIDTH * 0.45), type: WidthType.DXA },
          children: [
            new Paragraph({
              spacing: { after: 0 },
              children: [new TextRun({ text: "Nơi nhận:", font: FONT_MAIN, size: FONT_SIZE_SMALL, bold: true, italics: true })],
            }),
            new Paragraph({
              spacing: { after: 0 },
              children: [new TextRun({ text: `- ${data.Nguoi_Nhan || "Như trên"};`, font: FONT_MAIN, size: FONT_SIZE_SMALL, italics: true })],
            }),
            new Paragraph({
              spacing: { after: 0 },
              children: [new TextRun({ text: "- Lưu VP.", font: FONT_MAIN, size: FONT_SIZE_SMALL, italics: true })],
            }),
          ],
        }),
        new TableCell({
          borders: NO_BORDERS,
          width: { size: Math.floor(CONTENT_WIDTH * 0.55), type: WidthType.DXA },
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({ text: data.Don_Vi_Ky || "PHÒNG QLTK", font: FONT_MAIN, size: FONT_SIZE_BODY, bold: true })],
            }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({ text: data.Chuc_Danh_Ky || "Trưởng phòng", font: FONT_MAIN, size: FONT_SIZE_BODY, italics: true })],
            }),
            // Khoảng trống ký tên
            new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: " " })] }),
            new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: " " })] }),
            new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: " " })] }),
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { after: 0 },
              children: [new TextRun({ text: data.Nguoi_Ky || "[Họ và tên người ký]", font: FONT_MAIN, size: FONT_SIZE_BODY, bold: true })],
            }),
          ],
        }),
      ],
    }),
  ],
});

children.push(signatureTable);

// ═══════════════════════════════════════════════════════════
// PHỤ LỤC: LOG TÍNH TOÁN
// ═══════════════════════════════════════════════════════════
if (data.Calculation_Logs && Array.isArray(data.Calculation_Logs) && data.Calculation_Logs.length > 0) {
  children.push(new Paragraph({ children: [new PageBreak()] }));
  children.push(
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 200 },
      children: [new TextRun({ text: "PHỤ LỤC: CHI TIẾT TÍNH TOÁN", font: FONT_MAIN, size: FONT_SIZE_TITLE, bold: true })],
    })
  );
  
  const logsTable = createCalculationLogsTable(data.Calculation_Logs);
  if (logsTable) children.push(logsTable);
}

// ═══════════════════════════════════════════════════════════
// TẠO DOCUMENT
// ═══════════════════════════════════════════════════════════

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT_MAIN, size: FONT_SIZE_BODY },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2013",  // en-dash
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
          {
            level: 1,
            format: LevelFormat.BULLET,
            text: "\u2022",  // bullet
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1440, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE_A4_WIDTH, height: PAGE_A4_HEIGHT },
          margin: { top: MARGIN_TOP, right: MARGIN_RIGHT, bottom: MARGIN_BOTTOM, left: MARGIN_LEFT },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [
                new TextRun({
                  text: data.Ten_Du_An ? `DỰ ÁN: ${data.Ten_Du_An}` : "",
                  font: FONT_MAIN,
                  size: FONT_SIZE_SMALL,
                  italics: true,
                  color: "808080",
                }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Trang ", font: FONT_MAIN, size: FONT_SIZE_SMALL, color: "808080" }),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT_MAIN, size: FONT_SIZE_SMALL, color: "808080" }),
              ],
            }),
          ],
        }),
      },
      children: children,
    },
  ],
});

// ═══════════════════════════════════════════════════════════
// XUẤT FILE .DOCX
// ═══════════════════════════════════════════════════════════

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  console.log(`\n═══════════════════════════════════════════════════`);
  console.log(`  ✅ THÀNH CÔNG!`);
  console.log(`  📁 File: ${outputPath}`);
  console.log(`  📐 Kích thước: ${(buffer.length / 1024).toFixed(1)} KB`);
  console.log(`  📄 A4 | ${FONT_MAIN} ${FONT_SIZE_BODY / 2}pt | Lề: T3cm P2cm`);
  console.log(`═══════════════════════════════════════════════════`);
}).catch((err) => {
  console.error(`❌ [LỖI] Không thể tạo file Word: ${err.message}`);
  process.exit(1);
});
