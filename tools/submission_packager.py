#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
submission_packager.py — Bộ Đóng Gói Hồ Sơ Đệ Trình Tổng Hợp & Chữ Ký Số SHA-256 (v1.0 Tier-1 Consultancy)
===========================================================================================================
Tự động tập hợp toàn bộ các tệp hồ sơ giao nộp của dự án (Thuyết minh Word .docx, Phụ lục tính toán,
Bảng tính đối soát Excel .xlsx, Báo cáo thẩm tra & Hồ sơ khoanh lỗi CAD), tính toán mã băm kiểm chứng
toàn vẹn dữ liệu `SHA-256` cho từng tệp và xuất:
  1. `00_TO_KHAI_DE_TRINH_HO_SO.md` / `.docx` (Document Transmittal Sheet chuẩn ISO 19650).
  2. `SUBMISSION_MANIFEST_SHA256.json` (Biên bản khóa toàn vẹn dữ liệu chống chỉnh sửa sau thẩm định).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_submission_transmittal(
    files: List[str],
    output_dir: str,
    project_name: str = "Dự án Đầu tư Xây dựng Công trình",
    package_code: str = "SUB-PKG-2026-001",
    client_name: str = "Chủ Đầu Tư / Ban Quản Lý Dự Án",
    consultant_name: str = "Đơn vị Tư vấn Thiết kế & Thẩm tra (.agents v7.1)",
    purpose: str = "TRÌNH DUYỆT KỸ THUẬT & THẨM ĐỊNH (FOR APPROVAL)",
) -> Dict[str, Any]:
    """Tạo Hồ sơ Đệ trình Tổng hợp (Document Transmittal Sheet + SHA-256 Manifest)."""
    os.makedirs(output_dir, exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []

    for idx, fp in enumerate(files, 1):
        if not os.path.exists(fp):
            continue
        p = Path(fp).resolve()
        sha = compute_sha256(str(p))
        size_kb = round(p.stat().st_size / 1024.0, 2)
        ext = p.suffix.lower()
        doc_type = (
            "Thuyết minh / Báo cáo Word (.docx)" if ext == ".docx"
            else ("Bảng tính Kỹ thuật Excel (.xlsx)" if ext in (".xlsx", ".xlsm")
            else ("Sơ đồ / Bản vẽ Kỹ thuật (.png/.pdf)" if ext in (".png", ".pdf", ".dxf")
            else "Tài liệu Kỹ thuật"))
        )
        records.append({
            "stt": idx,
            "file_name": p.name,
            "doc_type": doc_type,
            "size_kb": size_kb,
            "sha256": sha,
            "short_sha256": sha[:16].upper(),
            "abs_path": str(p),
        })

    manifest = {
        "package_code": package_code,
        "project_name": project_name,
        "client_name": client_name,
        "consultant_name": consultant_name,
        "purpose": purpose,
        "issued_at": now_str,
        "standard_compliance": "ISO 19650 / TCVN 5574:2018 / TCVN 5575:2024 / TT 34/2026/TT-BXD",
        "total_deliverables": len(records),
        "deliverables": records,
    }

    manifest_path = os.path.join(output_dir, "SUBMISSION_MANIFEST_SHA256.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Render Markdown Transmittal Sheet
    md_lines = [
        f"# TỜ KHAI ĐỆ TRÌNH & BÀN GIAO HỒ SƠ KỸ THUẬT (DOCUMENT TRANSMITTAL SHEET)",
        f"**Mã bộ hồ sơ:** `{package_code}` | **Ngày phát hành:** {now_str}",
        "",
        "## 1. THÔNG TIN CHUNG VỀ ĐỢT ĐỆ TRÌNH",
        f"- **Dự án / Công trình:** {project_name}",
        f"- **Kính gửi (Chủ đầu tư / BQLDA):** {client_name}",
        f"- **Đơn vị đệ trình:** {consultant_name}",
        f"- **Mục đích đệ trình:** **{purpose}**",
        f"- **Tổng số tệp hồ sơ bàn giao:** {len(records)} tệp (đã khóa mã kiểm chứng toàn vẹn `SHA-256`)",
        "",
        "## 2. DANH MỤC HỒ SƠ BÀN GIAO & MÃ BĂM KIỂM CHỨNG TOÀN VẸN (SHA-256)",
        "",
        "| STT | Tên Tệp Hồ sơ Giao nộp | Phân loại Tài liệu | Dung lượng (KB) | Mã Băm SHA-256 (16 ký tự đầu) | Trạng thái Kiểm định |",
        "| :---: | :--- | :--- | :---: | :---: | :---: |",
    ]
    for r in records:
        md_lines.append(
            f"| {r['stt']} | `{r['file_name']}` | {r['doc_type']} | {r['size_kb']:,.1f} | `{r['short_sha256']}` | **[ĐÃ NIÊM PHONG SHA-256]** |"
        )

    md_lines.extend([
        "",
        "## 3. XÁC NHẬN BÀN GIAO & TIẾP NHẬN HỒ SƠ",
        "",
        "| Đại diện Bên Giao (Đơn vị Tư vấn) | Kiểm soát Chất lượng (QA/QC) | Đại diện Bên Nhận (Chủ đầu tư / TVGS) |",
        "| :---: | :---: | :---: |",
        "| *(Ký, ghi rõ họ tên & đóng dấu)* | *(Đã kiểm tra khớp mã SHA-256)* | *(Ký xác nhận tiếp nhận hồ sơ)* |",
        "",
    ])

    transmittal_md_path = os.path.join(output_dir, "00_TO_KHAI_DE_TRINH_HO_SO.md")
    Path(transmittal_md_path).write_text("\n".join(md_lines), encoding="utf-8")

    return {
        "manifest_json": manifest_path,
        "transmittal_md": transmittal_md_path,
        "total_files": len(records),
        "manifest": manifest,
    }


def main():
    parser = argparse.ArgumentParser(description="Submission Packager v1.0 — Đóng gói Hồ sơ Đệ trình & SHA-256")
    parser.add_argument("--files", "-f", nargs="+", required=True, help="Danh sách đường dẫn các file cần đóng gói")
    parser.add_argument("--output-dir", "-o", required=True, help="Thư mục xuất Tờ khai Đệ trình & Manifest")
    parser.add_argument("--project", default="Dự án Đầu tư Xây dựng Công trình", help="Tên dự án")
    parser.add_argument("--code", default="SUB-PKG-2026-001", help="Mã bộ hồ sơ đệ trình")
    args = parser.parse_args()

    res = build_submission_transmittal(args.files, args.output_dir, project_name=args.project, package_code=args.code)
    print(json.dumps({"status": "SUCCESS", "transmittal_md": res["transmittal_md"], "manifest_json": res["manifest_json"], "total_files": res["total_files"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
